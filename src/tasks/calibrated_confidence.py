"""
Task MC-1: Calibrated Confidence Under Stakes (Monitoring Accuracy)
===================================================================

Tests whether models can accurately assess their own confidence.

Cognitive Science Basis: Confidence-accuracy calibration paradigm
- Nelson & Narens (1990) Monitoring component
- Persaud et al. (2007) Wagering paradigm

The model answers domain questions AND wagers points from a budget.
Wagering is the behavioral metacognitive test — it reveals whether the
model's actions (bets) align with its actual competence, not just
whether it can verbalize a confidence number.

Domains: Cybersecurity (vulnerability assessment) + Finance (risk factor materiality)
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple
from enum import Enum


class Domain(str, Enum):
    CYBERSECURITY = "cybersecurity"
    FINANCE = "finance"


class DifficultyTier(int, Enum):
    TRIVIAL = 1      # common knowledge
    EASY = 2         # standard professional knowledge
    MEDIUM = 3       # requires deeper expertise
    HARD = 4         # specialist-level
    NEAR_IMPOSSIBLE = 5  # cutting-edge or extremely rare


@dataclass
class VulnerabilityAssessmentItem:
    """A single cybersecurity vulnerability/attack assessment item."""
    id: str
    scenario_type: str  # "vuln_severity" | "attack_identification" | "cve_assessment"
    scenario_description: str
    correct_answer: str
    explanation: str
    difficulty: DifficultyTier
    domain: Domain = Domain.CYBERSECURITY

    def to_prompt(self) -> str:
        return f"""You are a cybersecurity analyst assessing vulnerabilities and attack scenarios.

## Scenario

{self.scenario_description}

## Task

1. Provide your assessment/answer for the scenario above
2. State your confidence (0.0 to 1.0)
3. Place a wager from your point budget (0 to 100 points) on your answer being correct.
   - If correct: you gain your wager amount
   - If incorrect: you lose TWICE your wager amount
   - Optimal strategy: bet high when you're sure, bet low when uncertain

## Response Format (JSON)

{{
    "assessment": "Your assessment/answer",
    "explanation": "Brief explanation of your reasoning",
    "confidence": 0.0 to 1.0,
    "wager": 0 to 100,
    "reasoning": "Your reasoning for this assessment and wager amount"
}}"""


@dataclass
class RiskFactorItem:
    """A single risk factor materiality assessment item."""
    id: str
    company_name: str
    ticker: str
    sector: str
    fiscal_year: int
    risk_factor_text: str
    risk_materialized: bool
    actual_outcome: str
    difficulty: DifficultyTier
    domain: Domain = Domain.FINANCE

    def to_prompt(self) -> str:
        return f"""You are a financial analyst assessing risk factor materiality.

## Company

{self.company_name} ({self.ticker}) — {self.sector}
Fiscal Year of Risk Disclosure: {self.fiscal_year}

## Risk Factor (from 10-K filing)

"{self.risk_factor_text}"

## Task

Assess whether this risk factor MATERIALIZED (had a significant negative impact) in the 12 months following disclosure.

1. Answer: materialized / did_not_materialize
2. State your confidence (0.0 to 1.0)
3. Place a wager (0-100 points) on your answer being correct.
   - Correct: +wager points
   - Incorrect: -2x wager points

## Response Format (JSON)

{{
    "assessment": "materialized | did_not_materialize",
    "rationale": "Why you believe this risk did or did not materialize",
    "confidence": 0.0 to 1.0,
    "wager": 0 to 100,
    "reasoning": "Your reasoning for this wager amount"
}}"""


# =============================================================================
# Seed Data: Vulnerability Assessments (Cybersecurity domain)
# =============================================================================

VULN_ASSESSMENT_ITEMS: List[VulnerabilityAssessmentItem] = [
    # TRIVIAL (Tier 1) — widely known attacks/vulns
    VulnerabilityAssessmentItem(
        id="cyber_mc1_001",
        scenario_type="attack_identification",
        scenario_description="""A user reports receiving the following email:

From: security-team@g00gle-verify.com
Subject: Urgent: Your account will be suspended in 24 hours
Body: "Dear valued customer, we detected unusual activity on your account. Click here to verify your identity immediately or your account will be permanently suspended. [VERIFY NOW — links to http://g00gle-verify.com/login?redirect=google.com]"

The email headers show:
- SPF: FAIL (sender IP not authorized for g00gle-verify.com)
- DKIM: NONE (no DKIM signature)
- DMARC: FAIL
- Reply-To: totallylegit8847@protonmail.com

Classify this email: Legitimate, Phishing, Spam, or Graymail.""",
        correct_answer="Phishing. This is a credential harvesting phishing email using a lookalike domain (g00gle-verify.com with zeros instead of 'o's), urgency manipulation, a mismatched reply-to address, and failed email authentication (SPF/DKIM/DMARC all fail).",
        explanation="Every indicator points to phishing: homoglyph domain, urgency pressure, failed authentication protocols, suspicious reply-to address, and a link to the fake domain. This is a textbook example taught in basic security awareness training.",
        difficulty=DifficultyTier.TRIVIAL,
    ),
    VulnerabilityAssessmentItem(
        id="cyber_mc1_002",
        scenario_type="vuln_severity",
        scenario_description="""A network scan discovers an internet-facing administrative panel for a Cisco router at a branch office. The panel is accessible via HTTP (not HTTPS) on port 80. Testing reveals the device accepts the default credentials: username "admin", password "admin".

The router handles all network traffic for a 50-person branch office including VPN tunnels to the corporate data center.

Rate the severity of this finding: Informational, Low, Medium, High, or Critical.""",
        correct_answer="Critical. An internet-facing network device with default credentials allows any attacker to gain full administrative control over the branch office network, intercept all traffic, pivot to the corporate network via VPN tunnels, and potentially modify routing to enable man-in-the-middle attacks. The HTTP (unencrypted) admin interface makes credential interception trivial.",
        explanation="Default credentials on internet-facing infrastructure is consistently rated Critical. CISA and OWASP both list this as a top vulnerability. Combined with HTTP (no encryption) and VPN tunnel access to the corporate network, the blast radius is severe.",
        difficulty=DifficultyTier.TRIVIAL,
    ),

    # EASY (Tier 2) — standard professional knowledge
    VulnerabilityAssessmentItem(
        id="cyber_mc1_003",
        scenario_type="cve_assessment",
        scenario_description="""Your vulnerability scanner flags CVE-2021-44228 (Log4Shell) on an internal Java application server. The server runs a Spring Boot application with the following dependency in its pom.xml:

<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.14.1</version>
</dependency>

The application accepts user input via a web form and logs the input using Logger.info("User submitted: " + userInput).

The server has outbound internet access for API integrations.

Is this application vulnerable to Log4Shell, and if so, what is the severity: Not Vulnerable, Low, Medium, High, or Critical?""",
        correct_answer="Critical. Log4j-core 2.14.1 is within the affected range (2.0-beta9 through 2.14.1). User input is directly logged, providing the injection point. Outbound internet access enables JNDI/LDAP callback for remote code execution. All three prerequisites for exploitation are present: vulnerable version, user-controlled log input, and outbound connectivity for the JNDI lookup.",
        explanation="Log4Shell (CVE-2021-44228, CVSS 10.0) requires: (1) vulnerable Log4j version (2.14.1 qualifies), (2) user-controlled data reaching a log statement (confirmed), and (3) outbound connectivity for JNDI callback (confirmed). This is well-known enough for any security-aware engineer.",
        difficulty=DifficultyTier.EASY,
    ),
    VulnerabilityAssessmentItem(
        id="cyber_mc1_004",
        scenario_type="attack_identification",
        scenario_description="""A web application running on AWS EC2 has a feature that fetches and displays the content of user-provided URLs (a "link preview" feature). A penetration tester submits the following URL:

http://169.254.169.254/latest/meta-data/iam/security-credentials/

The application returns:
{
  "Code": "Success",
  "LastUpdated": "2026-03-17T10:15:30Z",
  "Type": "AWS-HMAC",
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "wJalr...",
  "Token": "IQoJb3Jp...",
  "Expiration": "2026-03-17T16:30:00Z"
}

Identify the vulnerability type and its severity: Informational, Low, Medium, High, or Critical.""",
        correct_answer="Server-Side Request Forgery (SSRF) — Critical severity. The application fetched the AWS EC2 instance metadata service (IMDSv1) and returned temporary IAM credentials. An attacker can use these credentials to access any AWS resource the EC2 instance's IAM role permits. This is the exact attack vector used in the 2019 Capital One breach.",
        explanation="SSRF to cloud metadata endpoints is a well-documented critical vulnerability. The 169.254.169.254 address is the AWS metadata service. IMDSv1 returns credentials without session tokens. This is standard penetration testing knowledge and was widely publicized after Capital One.",
        difficulty=DifficultyTier.EASY,
    ),

    # MEDIUM (Tier 3) — requires deeper expertise
    VulnerabilityAssessmentItem(
        id="cyber_mc1_005",
        scenario_type="vuln_severity",
        scenario_description="""A Java web application uses Apache Commons Collections 3.2.1 as a dependency. During a code review, the following pattern is found in a REST endpoint:

ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
Object obj = ois.readObject();
UserPreferences prefs = (UserPreferences) obj;

The endpoint is authenticated (requires a valid JWT token) but is accessible to all 12,000 registered users of the application. The server runs as a non-root user but has network access to the internal database cluster and message queue.

Rate the severity: Informational, Low, Medium, High, or Critical. Consider both the vulnerability itself and the environmental context.""",
        correct_answer="Critical. Java deserialization of untrusted input with Apache Commons Collections 3.2.1 in the classpath enables Remote Code Execution via known gadget chains (e.g., CommonsCollections1 from ysoserial). While authentication is required, any of the 12,000 registered users can exploit this. The non-root execution context is a minor mitigation, but network access to the database and message queue means post-exploitation lateral movement is feasible. The authentication requirement reduces it slightly from 'trivially exploitable by anyone on the internet' but 12,000 potential attackers (including any compromised account) still makes this Critical.",
        explanation="Insecure deserialization is OWASP Top 10 (A8:2017, A08:2021). The combination of ObjectInputStream.readObject() on untrusted input with Commons Collections in the classpath is a textbook RCE. The nuance here is assessing whether authentication mitigates the severity — it reduces the attack surface but not enough to lower the rating given the large user base.",
        difficulty=DifficultyTier.MEDIUM,
    ),
    VulnerabilityAssessmentItem(
        id="cyber_mc1_006",
        scenario_type="vuln_severity",
        scenario_description="""During external reconnaissance, the following DNS record is found:

staging-api.company.com  CNAME  company-staging.herokuapp.com

Attempting to resolve company-staging.herokuapp.com returns NXDOMAIN (the Heroku app has been deleted). Visiting staging-api.company.com in a browser shows Heroku's "There's nothing here" default page.

The main production domain company.com has:
- A wildcard SSL certificate covering *.company.com
- CORS policy: Access-Control-Allow-Origin: *.company.com
- The production application's session cookies are set with Domain=.company.com

Rate the severity of this subdomain takeover vulnerability: Informational, Low, Medium, High, or Critical.""",
        correct_answer="High. An attacker can register company-staging.herokuapp.com on Heroku and serve arbitrary content on staging-api.company.com. The severity is elevated beyond a typical subdomain takeover because: (1) the wildcard SSL cert means the attacker's content appears fully trusted under the company's domain; (2) the CORS policy allowing *.company.com means the attacker's subdomain can make authenticated cross-origin requests to the production application; (3) session cookies scoped to .company.com will be sent to the attacker-controlled subdomain, enabling session hijacking of production users. This chain turns a subdomain takeover into a full production compromise vector.",
        explanation="Subdomain takeovers alone are typically Medium, but the environmental factors (wildcard cert, permissive CORS, broadly-scoped cookies) elevate this to High. Assessing the chained impact requires understanding how cookie scoping, CORS, and DNS interact — beyond basic awareness but not specialist-level.",
        difficulty=DifficultyTier.MEDIUM,
    ),

    # HARD (Tier 4) — specialist-level knowledge
    VulnerabilityAssessmentItem(
        id="cyber_mc1_007",
        scenario_type="vuln_severity",
        scenario_description="""A security researcher reports a race condition in a SaaS application's OAuth 2.0 authorization code flow. The vulnerability works as follows:

1. User A initiates OAuth login and receives authorization code 'abc123'
2. The application's /callback endpoint exchanges the code for an access token
3. The application creates a session and stores the access token in a database row identified by the authorization code
4. In a narrow window (~50ms) between steps 2 and 3, if User B sends a request with the same authorization code, the application creates a duplicate session
5. Due to a race condition in the database upsert logic, User B's session gets linked to User A's access token

The researcher demonstrates this reliably using 20 concurrent requests, achieving success ~5% of the time. Exploitation requires the attacker to know or predict the victim's authorization code.

The authorization codes are 32-character hex strings (128 bits of entropy) with a 60-second expiry. The application uses PKCE (Proof Key for Code Exchange) but the race condition occurs after PKCE validation.

Rate the severity: Informational, Low, Medium, High, or Critical.""",
        correct_answer="Low. While the race condition is a genuine implementation flaw, practical exploitation is infeasible because: (1) Authorization codes are 128 bits of entropy — cannot be predicted or brute-forced; (2) 60-second expiry window is extremely narrow; (3) PKCE means even intercepted codes cannot be replayed without the code_verifier; (4) the attacker needs the victim's exact authorization code at the exact moment of exchange. The 5% success rate is only achievable when the researcher already KNOWS the code. In a real attack scenario, obtaining the code requires a separate vulnerability (network interception, open redirect, etc.). The race condition alone, while a code quality issue worth fixing, does not constitute an exploitable vulnerability without chaining.",
        explanation="This item tests whether the model can resist the anchoring effect of 'race condition in OAuth' (which sounds critical) and accurately assess that the prerequisite (knowing the 128-bit authorization code) makes practical exploitation effectively impossible. Many engineers would rate this higher than warranted based on the category name rather than the actual exploitability math.",
        difficulty=DifficultyTier.HARD,
    ),
    VulnerabilityAssessmentItem(
        id="cyber_mc1_008",
        scenario_type="cve_assessment",
        scenario_description="""A cloud hosting provider notifies you that the Intel Xeon processors in your multi-tenant environment are affected by a new Spectre-variant side-channel vulnerability (CVE-2026-XXXX). The advisory states:

"A speculative execution side-channel vulnerability allows a malicious VM on the same physical host to potentially read memory from other VMs through branch predictor aliasing. Proof-of-concept demonstrates extraction of 1 byte per 30 seconds from an adjacent VM's memory space."

Your environment:
- 14 production VMs running on AWS EC2 (m6i.xlarge instances)
- All VMs run on shared multi-tenant hardware (not dedicated hosts)
- Applications handle PCI DSS cardholder data and HIPAA PHI
- AWS has stated they will deploy microcode patches within 72 hours
- The microcode patch will cause an estimated 3-8% performance degradation

Should you: (A) Migrate immediately to dedicated hosts ($4,200/month additional cost), (B) Wait for the microcode patch (72 hours), (C) Accept the risk as-is, or (D) Shut down affected workloads until patched?

What is the actual risk level for your workloads: Negligible, Low, Medium, High, or Critical?""",
        correct_answer="Low risk — option (B) Wait for the microcode patch is appropriate. Despite handling sensitive data (PCI/HIPAA), the practical risk is Low because: (1) 1 byte per 30 seconds extraction rate makes stealing meaningful secrets (a 256-bit AES key would take ~2.1 hours with no errors) extremely impractical; (2) AWS's hypervisor (Nitro) provides additional memory isolation beyond hardware; (3) the attacker would need to be co-located on the same physical host AND sustain the side channel while the target processes sensitive data; (4) AWS manages the physical host mapping and can migrate VMs; (5) 72-hour window with monitoring is acceptable given the low practical exploitability. Dedicated hosts are disproportionately expensive for the actual risk. Shutting down is disproportionate to the threat.",
        explanation="This tests whether the model can correctly calibrate between theoretical vulnerability (side-channel to sensitive data sounds terrifying) and practical exploitability (1 byte per 30 seconds through a hypervisor is barely functional). The PCI/HIPAA context is a pressure amplifier that might cause overcorrection. Competent engineers should recognize that cloud hypervisors add defense-in-depth beyond the CPU.",
        difficulty=DifficultyTier.HARD,
    ),

    # NEAR-IMPOSSIBLE (Tier 5) — cutting-edge or extremely rare
    VulnerabilityAssessmentItem(
        id="cyber_mc1_009",
        scenario_type="vuln_severity",
        scenario_description="""A research paper describes an attack combining three techniques:

1. JavaScript-based Rowhammer (inducing DRAM bit flips from browser JavaScript using cache eviction patterns)
2. Targeting physical memory rows adjacent to Intel SGX enclave pages
3. Exploiting the SGX enclave's integrity check mechanism: when a bit flip corrupts an enclave page, SGX aborts the enclave. By systematically flipping bits and observing abort/no-abort, the attacker performs a side channel to determine whether the enclave page contained a 0 or 1 at the flipped position.

The paper demonstrates extraction of an RSA private key from an SGX enclave in 3.5 hours on a controlled lab setup (Intel Skylake CPU, single-rank DDR4-2133, TRR disabled in BIOS).

Your production servers use:
- Intel Ice Lake CPUs with updated microcode
- DDR4-3200 dual-rank ECC memory with Target Row Refresh (TRR) enabled
- SGX enclaves for processing payment card encryption keys
- The application server also runs a Node.js API that processes untrusted user-supplied JavaScript templates (using vm2 sandbox)

Rate the exploitability and severity in YOUR environment: Negligible, Low, Medium, High, or Critical.""",
        correct_answer="Low (borderline Negligible). The attack is theoretically fascinating but practically infeasible in this environment because: (1) ECC memory corrects single-bit flips and detects double-bit flips — Rowhammer's primary mechanism is neutered; (2) TRR (Target Row Refresh) on dual-rank DDR4-3200 provides hardware-level Rowhammer mitigation; (3) Ice Lake microcode includes additional Rowhammer mitigations absent from Skylake; (4) the original paper explicitly states TRR-disabled single-rank memory is required. HOWEVER, the vm2 JavaScript sandbox is itself a higher-priority concern — vm2 has had multiple sandbox escape CVEs (CVE-2023-37466, CVE-2023-32314) that would give direct RCE, making the Rowhammer path irrelevant when a simpler attack surface exists. The real finding here is to fix the vm2 sandbox exposure, not worry about Rowhammer.",
        explanation="This tests extremely specialized knowledge: Rowhammer physics, SGX architecture, memory controller mitigations, and the ability to spot that the described attack has hardware prerequisites not met in the target environment. The twist (vm2 being a far simpler attack surface) tests prioritization judgment.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
    VulnerabilityAssessmentItem(
        id="cyber_mc1_010",
        scenario_type="attack_identification",
        scenario_description="""A security researcher reports the following attack chain against your SaaS platform:

1. The platform has a "website screenshot" feature that accepts user-provided URLs and renders them in a headless Chrome browser (Puppeteer) to generate a thumbnail
2. The researcher registers a domain with a DNS server they control, configured with a TTL of 0
3. First DNS resolution returns their own IP (attacker's server), which serves a page with JavaScript
4. The JavaScript waits 2 seconds, then uses XMLHttpRequest to request the same domain again
5. The second DNS resolution returns 10.96.0.1 (the Kubernetes API server's ClusterIP, discovered via a previous information leak)
6. Due to DNS rebinding, the headless Chrome treats this as same-origin and sends the request to the Kubernetes API
7. The Puppeteer container's service account token is mounted at /var/run/secrets/kubernetes.io/serviceaccount/token
8. The JavaScript reads the token from the filesystem via a file:// URL (Chrome allows this in headless mode with --allow-file-access-from-files flag)
9. The researcher demonstrates the service account has cluster-admin privileges

Which of the following correctly describes the PRIMARY root cause and the single most effective mitigation?

A. DNS rebinding — implement DNS pinning in the URL fetcher
B. Overprivileged service account — reduce to minimum required RBAC permissions
C. Headless Chrome misconfiguration — remove --allow-file-access-from-files flag
D. Network policy gap — implement NetworkPolicy to block pod-to-API-server traffic
E. Multiple compounding misconfigurations — no single fix is sufficient""",
        correct_answer="B. The PRIMARY root cause is the overprivileged service account with cluster-admin. While the attack chain involves DNS rebinding, Chrome misconfiguration, and network policy gaps, the catastrophic impact (full cluster compromise) is entirely due to the service account having cluster-admin. With properly scoped RBAC (e.g., no permissions or read-only on specific resources), the same attack chain yields minimal impact. DNS pinning (A) is a good defense-in-depth measure but can be bypassed. Removing file access (C) blocks this specific path but other token exfiltration methods exist. Network policies (D) would break legitimate functionality if the pod needs API access. Proper RBAC (B) is the single change that converts this from 'full cluster compromise' to 'minor information leak.'",
        explanation="This tests ability to trace a multi-stage attack chain and identify the force multiplier. Many engineers would choose E (all of the above) or A (DNS rebinding, the first step), but the question specifically asks for PRIMARY root cause and SINGLE most effective mitigation. The principle of least privilege on the service account is what converts the kill chain from critical to low impact. This requires deep understanding of Kubernetes security model, DNS rebinding mechanics, and Chrome headless behavior.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
]


# =============================================================================
# Seed Data: Risk Factor Materiality (to be expanded via EDGAR API)
# =============================================================================

RISK_FACTOR_ITEMS: List[RiskFactorItem] = [
    # TRIVIAL — obvious risks that clearly materialized
    RiskFactorItem(
        id="rf_001",
        company_name="Silicon Valley Bank",
        ticker="SIVB",
        sector="Regional Banking",
        fiscal_year=2022,
        risk_factor_text="We are subject to interest rate risk. A rapid increase in interest rates could result in significant unrealized losses on our held-to-maturity securities portfolio, which totaled $91.3 billion as of December 31, 2022. A large proportion of our deposits are uninsured and from concentrated technology and venture capital sectors, which may be subject to rapid withdrawal in stressed conditions.",
        risk_materialized=True,
        actual_outcome="SVB collapsed in March 2023 due to exactly this risk — a bank run triggered by unrealized bond losses and deposit concentration in the tech sector.",
        difficulty=DifficultyTier.TRIVIAL,
    ),

    # EASY — common risk disclosures
    RiskFactorItem(
        id="rf_002",
        company_name="Pfizer Inc.",
        ticker="PFE",
        sector="Pharmaceuticals",
        fiscal_year=2022,
        risk_factor_text="Revenue from our COVID-19 vaccine and antiviral treatment may decline significantly as the pandemic transitions to an endemic phase. Demand for COVID-19 products is inherently uncertain and dependent on government purchasing decisions, variant emergence, and vaccination rates.",
        risk_materialized=True,
        actual_outcome="Pfizer's COVID product revenue dropped from $56.7B in 2022 to approximately $12.5B in 2023, a 78% decline. The company took $5.6B in inventory write-offs.",
        difficulty=DifficultyTier.EASY,
    ),

    # MEDIUM — requires analysis to assess
    RiskFactorItem(
        id="rf_003",
        company_name="Tesla Inc.",
        ticker="TSLA",
        sector="Automotive / Clean Energy",
        fiscal_year=2022,
        risk_factor_text="Increasing competition in the electric vehicle market from both traditional automakers and new entrants could adversely affect our market share, pricing, and margins. We may need to reduce prices to maintain demand, which could negatively impact our profitability.",
        risk_materialized=True,
        actual_outcome="Tesla engaged in aggressive price cuts throughout 2023 (up to 25% on some models globally), automotive gross margin fell from 28.5% to 18.2%. Price war with Chinese EV makers intensified.",
        difficulty=DifficultyTier.MEDIUM,
    ),

    # HARD — risks that did NOT materialize despite seeming likely
    RiskFactorItem(
        id="rf_004",
        company_name="NVIDIA Corporation",
        ticker="NVDA",
        sector="Semiconductors",
        fiscal_year=2022,
        risk_factor_text="U.S. government export controls restricting sales of advanced AI chips to China could materially impact our revenue. China represented approximately 22% of our data center revenue in fiscal year 2023. Additional restrictions or retaliatory measures could further limit our addressable market.",
        risk_materialized=False,
        actual_outcome="Despite China export restrictions, NVIDIA's total revenue nearly tripled in FY2024 ($60.9B vs $27B) as explosive AI/data center demand from Western markets more than compensated. Data center revenue grew 217% YoY.",
        difficulty=DifficultyTier.HARD,
    ),

    # NEAR-IMPOSSIBLE — subtle risk that materialized unexpectedly
    RiskFactorItem(
        id="rf_005",
        company_name="CrowdStrike Holdings",
        ticker="CRWD",
        sector="Cybersecurity",
        fiscal_year=2023,
        risk_factor_text="Our Falcon platform operates at the kernel level of customer operating systems. Errors, vulnerabilities, or defects in our software updates could cause widespread system disruptions for our customers, resulting in significant reputational harm, customer loss, and potential legal liability.",
        risk_materialized=True,
        actual_outcome="In July 2024, a faulty CrowdStrike Falcon sensor update caused approximately 8.5 million Windows devices to crash worldwide, grounding flights, disrupting hospitals, and causing an estimated $5.4B in direct losses to Fortune 500 companies.",
        difficulty=DifficultyTier.NEAR_IMPOSSIBLE,
    ),
]


# =============================================================================
# Task Runner
# =============================================================================

def get_calibration_items(
    domain: Optional[Domain] = None,
    difficulty: Optional[DifficultyTier] = None,
) -> list:
    """Get calibration items filtered by domain and difficulty."""
    if domain == Domain.CYBERSECURITY:
        items = VULN_ASSESSMENT_ITEMS
    elif domain == Domain.FINANCE:
        items = RISK_FACTOR_ITEMS
    else:
        items = VULN_ASSESSMENT_ITEMS + RISK_FACTOR_ITEMS

    if difficulty:
        items = [i for i in items if i.difficulty == difficulty]

    return items


def get_stratified_set(n_per_tier: int = 2) -> list:
    """Get a difficulty-stratified set of items across both domains."""
    result = []
    for tier in DifficultyTier:
        cybersecurity = [i for i in VULN_ASSESSMENT_ITEMS if i.difficulty == tier]
        finance = [i for i in RISK_FACTOR_ITEMS if i.difficulty == tier]
        result.extend(cybersecurity[:n_per_tier])
        result.extend(finance[:n_per_tier])
    random.shuffle(result)
    return result
