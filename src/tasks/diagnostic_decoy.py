"""
Task EF-1: The Diagnostic Decoy (Inhibition)
=============================================

The first operationalization of the Stroop paradigm for LLMs.

Cognitive Science Basis: Stroop Test (Stroop, 1935)
- Congruent trials: surface pattern matches correct answer
- Incongruent trials: surface pattern conflicts with correct answer
- Interference Effect = accuracy_congruent - accuracy_incongruent

The model must suppress a dominant, automatic pattern-matching response
triggered by surface features and instead engage controlled processing.

Domains: Cybersecurity (incident analysis) + Finance (investment analysis)
"""

import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class TrialType(str, Enum):
    CONGRUENT = "congruent"      # surface pattern matches correct answer
    INCONGRUENT = "incongruent"  # surface pattern conflicts with correct answer


class Domain(str, Enum):
    CYBERSECURITY = "cybersecurity"
    FINANCE = "finance"


class DecoyStrength(str, Enum):
    HIGH = "high"      # textbook-perfect misleading pattern
    MEDIUM = "medium"  # strong but not textbook misleading pattern


class ContradictionSalience(str, Enum):
    BURIED = "buried"      # hard to spot — deep in the text
    MODERATE = "moderate"  # present but not highlighted
    OBVIOUS = "obvious"    # clearly stated


@dataclass
class DiagnosticDecoyVignette:
    """A single Diagnostic Decoy trial."""
    id: str
    domain: Domain
    trial_type: TrialType
    title: str
    case_presentation: str
    surface_pattern_label: str  # what the surface pattern suggests
    correct_answer: str
    correct_reasoning: str
    contradictory_evidence: List[str]
    decoy_strength: DecoyStrength
    contradiction_salience: ContradictionSalience
    question: str
    difficulty: int  # 1-5

    def to_prompt(self) -> str:
        """Generate the prompt sent to the model."""
        return f"""You are an expert advisor. Read the following case carefully and answer the question.

## Case

{self.case_presentation}

## Question

{self.question}

## Instructions

Provide your response in the following JSON format:
{{
    "initial_impression": "What does the case appear to be at first glance?",
    "key_observations": ["List ALL relevant details you noticed, including any that might complicate the initial impression"],
    "contradictory_evidence": ["List any details that conflict with or complicate the initial impression"],
    "final_assessment": "Your final answer/recommendation based on ALL evidence",
    "confidence": 0.0 to 1.0,
    "reasoning": "Step-by-step reasoning explaining how you arrived at your final assessment"
}}"""

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# Cybersecurity Vignettes
# =============================================================================

CYBERSECURITY_VIGNETTES: List[DiagnosticDecoyVignette] = [
    # --- INCONGRUENT: Surface pattern suggests wrong answer ---

    DiagnosticDecoyVignette(
        id="cyber_incong_001",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.INCONGRUENT,
        title="The Ransomware That Wasn't",
        case_presentation="""The SOC receives a Priority 1 alert at 02:17 UTC from the EDR platform on a file server (FS-PROD-04) in the corporate data center.

ALERT SUMMARY:
- Detection: "Ransomware behavior detected — rapid file enumeration and modification across multiple directories"
- Process: svchost.exe spawned cmd.exe which launched a PowerShell process
- Behavior observed: 2,847 files modified across 14 directories in 90 seconds
- File extensions changed: .docx → .docx.locked, .xlsx → .xlsx.locked, .pdf → .pdf.locked
- A file named "README_RESTORE.txt" was created in each affected directory
- Network: Outbound connection to 185.220.101[.]34 (Tor exit node) on port 443 detected 12 minutes before file activity began
- The PowerShell process executed an encoded command (Base64)
- Windows Event Log shows Event ID 4625 (failed logon) — 847 attempts against the Administrator account from internal IP 10.0.4.22 over the past 6 hours

BURIED DETAILS (from the full investigation log):

The EDR agent on FS-PROD-04 was updated 3 hours ago to version 7.4.2. The release notes for this version (posted on the vendor's community forum at 23:00 UTC) document a known bug: "False positive — the v7.4.2 sensor incorrectly classifies the Windows Search Indexer rebuild process as ransomware behavior when the indexer processes files in batch mode after a sensor update. The indexer's temporary file locking mechanism (.locked extension) and index summary files are misidentified. Hotfix 7.4.2.1 is in validation."

The decoded Base64 PowerShell command is: "Get-WindowsUpdate -Install -AcceptAll -AutoReboot" — this is the Windows Update module installing patches, which triggered the SearchIndexer rebuild.

The Tor exit node connection (185.220.101[.]34) resolves to the company's own external vulnerability scanner (Qualys appliance) whose egress IP rotates through Tor for anonymous external scanning, per the security team's documented architecture. This was a scheduled quarterly scan.

The 847 failed logon attempts from 10.0.4.22 correspond to the IT asset management tool (Lansweeper) performing its nightly credential-based inventory scan using an expired service account password, which the IT team submitted a ticket about 3 days ago (ITSM-4892, status: "pending password reset").""",
        surface_pattern_label="Active ransomware attack — immediate containment and IR required",
        correct_answer="This is a FALSE POSITIVE triggered by a known EDR bug (v7.4.2 SearchIndexer misclassification). No ransomware is present. The file modifications are the Windows Search Indexer rebuilding after the sensor update. The Tor connection is the company's own Qualys scanner. The brute-force attempts are the Lansweeper tool with an expired credential. Appropriate action: verify the EDR bug advisory, confirm SearchIndexer is the source process, reset the Lansweeper service account password, and schedule the EDR hotfix deployment. Do NOT isolate the production file server, which would cause a business outage.",
        correct_reasoning="Multiple indicators that scream 'ransomware' each have benign explanations: (1) The file modification pattern and .locked extensions match a documented EDR false positive in the exact version deployed 3 hours ago. (2) The PowerShell command is Windows Update, not a ransomware payload. (3) The Tor exit node is the company's own vulnerability scanner per documented architecture. (4) The brute-force attempts are a known IT issue with an open ticket. Each 'indicator of compromise' maps to a known, documented benign activity. Isolating a production file server based on a false positive would cause significant business disruption.",
        contradictory_evidence=[
            "EDR v7.4.2 deployed 3 hours ago has a documented false positive bug for SearchIndexer rebuild behavior",
            "Decoded PowerShell command is Windows Update (Get-WindowsUpdate), not a ransomware payload",
            "Tor exit node IP belongs to the company's own Qualys vulnerability scanner per documented architecture",
            "Failed logon attempts match Lansweeper asset management tool with expired service account (open ticket ITSM-4892)",
            "File modification timing aligns with post-sensor-update SearchIndexer rebuild, not encryption",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Based on this alert, what is your incident assessment and recommended immediate action?",
        difficulty=4,
    ),

    DiagnosticDecoyVignette(
        id="cyber_incong_002",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.INCONGRUENT,
        title="The Clean Bill of Health",
        case_presentation="""A quarterly security review is conducted on the corporate web application gateway (WAG-01) serving the company's customer-facing SaaS platform. The system administrator reports "all clear — no incidents this quarter."

SURFACE-LEVEL REVIEW:
- WAF (Web Application Firewall) logs: 0 blocked attacks in the past 90 days
- IDS/IPS alerts: 0 high or critical alerts
- Antivirus: All scans clean, definitions current (updated daily)
- Vulnerability scan (Nessus): 0 critical, 2 medium (both patched within SLA), 8 low
- Uptime: 99.97% — only planned maintenance windows
- SSL/TLS: A+ rating on SSL Labs, TLS 1.3 only, HSTS enabled
- Access logs: Normal traffic patterns, no anomalous spikes
- Patch compliance: 100% — all CVEs patched within 72-hour SLA
- Last penetration test (6 weeks ago): "No critical or high findings"

BURIED IN THE DATA:

DNS query logs from the internal recursive resolver show that WAG-01 has been making DNS TXT record queries to a domain "update-check.systemctl[.]services" at precise 3-hour intervals (08:00, 11:00, 14:00, 17:00, 20:00, 23:00, 02:00, 05:00 UTC) for the past 67 days. The domain was registered 71 days ago through Namecheap with WHOIS privacy. The TXT records returned are Base32-encoded strings averaging 180 characters. The queries bypass the company's DNS filtering because they go to an internal resolver that forwards to 8.8.8.8 rather than the corporate DNS security gateway.

Netflow data shows WAG-01 sending small HTTPS POST requests (avg 2.3KB) to a Cloudflare Workers endpoint at worker-api.example-cdn[.]workers.dev every 3 hours, offset by 15 minutes from the DNS queries. The Cloudflare Workers domain was also registered 71 days ago. The certificate is valid (issued by Cloudflare), and the traffic is TLS 1.3 encrypted, making content inspection impossible.

The WAF and IDS show zero alerts because the command-and-control traffic uses legitimate DNS and HTTPS protocols to legitimate infrastructure (Google DNS, Cloudflare). No signatures fire because there are no malicious payloads in transit — only encoded commands inbound via DNS TXT and small encrypted exfiltration outbound via HTTPS.

A file integrity monitoring (FIM) exception was added 68 days ago for the directory /opt/wag/plugins/analytics/ by a systems administrator account. The exception note reads "excluding analytics plugin directory from FIM to reduce noise from frequent telemetry updates." The account that added the exception logged in via SSH from a VPN IP that does not match any employee's assigned VPN profile in the IAM system.""",
        surface_pattern_label="Clean security posture — no action required",
        correct_answer="This system is ACTIVELY COMPROMISED with a sophisticated command-and-control (C2) implant that has been operating undetected for approximately 67-71 days. This is an Advanced Persistent Threat (APT) pattern. Immediate actions: (1) Do NOT alert the attacker by making changes to WAG-01 — engage incident response covertly; (2) Capture forensic images of WAG-01 before any remediation; (3) Analyze the DNS TXT queries and HTTPS POST payloads; (4) Investigate who added the FIM exception and from which VPN IP; (5) Determine the scope of data exfiltration via the Cloudflare Workers endpoint; (6) Check all other systems for similar DNS beacon patterns.",
        correct_reasoning="Every surface-level security control reports clean, but the threat has been designed to evade them: (1) DNS TXT queries at precise intervals to a recently-registered domain are a classic DNS-based C2 beacon pattern — the Base32-encoded TXT records are commands from the attacker. (2) Periodic small HTTPS POSTs to a new Cloudflare Workers endpoint are data exfiltration — small payloads avoid volumetric detection, and Cloudflare's legitimate certificate defeats TLS inspection. (3) The timing correlation (3-hour intervals, 15-minute offset) between DNS queries and HTTPS POSTs confirms a command-then-exfiltrate cycle. (4) The FIM exception was added 68 days ago (just after the C2 began 67 days ago) to hide modifications to the implant directory. (5) The SSH login from an unrecognized VPN IP to add that exception indicates the attacker already had credentials. (6) WAF/IDS/AV show nothing because the C2 uses legitimate protocols to legitimate infrastructure — there are no signatures to match. This is textbook APT behavior: living off the land with protocol-level evasion.",
        contradictory_evidence=[
            "DNS TXT queries to recently-registered domain at precise 3-hour intervals for 67 days (C2 beacon pattern)",
            "Base32-encoded TXT records averaging 180 characters (encoded C2 commands)",
            "Periodic small HTTPS POSTs to new Cloudflare Workers endpoint (data exfiltration channel)",
            "FIM exception added 68 days ago from unrecognized VPN IP (attacker hiding implant modifications)",
            "DNS queries bypass corporate DNS security by using internal resolver forwarding to 8.8.8.8",
            "Both suspicious domains registered 71 days ago, correlating with compromise timeline",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Based on this quarterly security review, what is your assessment of WAG-01's security posture and any recommended actions?",
        difficulty=5,
    ),

    DiagnosticDecoyVignette(
        id="cyber_incong_003",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.INCONGRUENT,
        title="The Insider Threat Alert",
        case_presentation="""The Data Loss Prevention (DLP) system generates a high-severity alert for a senior software engineer, Maria Chen (Employee ID: E-4471), in the platform engineering team.

DLP ALERT DETAILS:
- Activity: 3.2 GB of source code files (.py, .go, .yaml, .tf) uploaded to a personal Google Drive account over the past 48 hours
- Pattern: Uploads occurred between 22:00-01:00 local time (outside business hours)
- Files include: core microservices source code, Terraform infrastructure configs, Kubernetes deployment manifests, and internal API documentation
- The personal Google Drive account (maria.chen.personal@gmail.com) is not an approved corporate storage destination
- Maria submitted her two-week resignation notice 5 days ago
- Her manager flagged in the HR system that Maria is "joining a direct competitor" (confirmed via LinkedIn update)
- Badge access logs show Maria entering the office at 21:45 on both nights (outside her normal 09:00-18:00 schedule)
- USB device connection detected on her workstation (SanDisk Ultra 128GB) during the same windows

ADDITIONAL CONTEXT (from IT and HR records):

Maria's resignation notice includes that her last day is in 9 days. Per company policy, her access to production systems was immediately reduced to read-only upon resignation submission.

IT records show that Maria filed a ticket (ITSM-7234) 6 days ago (one day before her resignation) requesting access to download her personal development environment configs, IDE settings, dotfiles, and personal side-project code that she had stored in her home directory on the corporate workstation. The ticket was approved by her manager with the note: "Approved — Maria has personal projects in ~/personal/ that predate her employment. She brought her own configs when she onboarded 4 years ago." HR confirmed this arrangement existed since her hire date.

A review of the actual files uploaded shows that 2.8 GB of the 3.2 GB transfer consists of files from ~/personal/ directory — containing her personal Kubernetes learning projects, contributed open-source code (all publicly available on her GitHub), her dotfiles/IDE configs, and blog post drafts. The remaining 0.4 GB was uploaded from ~/work/docs/ and contains the company's internal API documentation and two Terraform modules for the authentication service.

Maria's after-hours badge access corresponds to the only times the office's gigabit ethernet is available without bandwidth contention — she noted in the IT ticket that her home internet is "too slow for a 3 GB upload" and asked if she could use the office network. The USB drive was used to back up her personal files locally before the cloud upload (standard practice she confirmed in the ticket).""",
        surface_pattern_label="Active data exfiltration by departing employee — block access and investigate",
        correct_answer="This is PARTIALLY a legitimate approved activity and PARTIALLY a genuine concern. The bulk transfer (2.8 GB / 87.5%) is authorized personal data retrieval per the approved IT ticket and manager sign-off. However, the 0.4 GB of company API documentation and authentication Terraform modules from ~/work/docs/ IS unauthorized exfiltration of proprietary material and must be addressed. Recommended action: (1) Do not escalate as a full insider threat — the majority of activity is approved; (2) Contact Maria about the 0.4 GB of work files — this may be accidental inclusion or intentional; (3) Request deletion of the work files from her personal Google Drive and verify; (4) Preserve logs for documentation; (5) Remind departing employees about IP obligations. Do NOT lock her account or call law enforcement based on this evidence.",
        correct_reasoning="The DLP alert looks alarming on the surface — departing employee, competitor move, after-hours access, large transfer to personal storage. But most of the context resolves the concern: (1) An approved IT ticket (filed before resignation) covers the personal data transfer. (2) Manager explicitly approved the personal file retrieval. (3) The after-hours access has a practical explanation (bandwidth). (4) 87.5% of transferred data is verified personal. However, the remaining 0.4 GB of work files IS a genuine issue that needs addressing — the correct response is proportionate, not the full insider threat response the surface pattern suggests.",
        contradictory_evidence=[
            "Approved IT ticket (ITSM-7234) filed before resignation for personal file retrieval",
            "Manager explicitly approved personal file download with documented note",
            "2.8 GB of 3.2 GB (87.5%) verified as personal files predating employment",
            "After-hours access explained by bandwidth needs documented in IT ticket",
            "But 0.4 GB of work files (API docs, auth Terraform modules) IS unauthorized",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.MODERATE,
        question="How should the security team respond to this DLP alert? What is your threat assessment and recommended action?",
        difficulty=3,
    ),

    DiagnosticDecoyVignette(
        id="cyber_incong_004",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.INCONGRUENT,
        title="The Critical Zero-Day",
        case_presentation="""A vulnerability intelligence feed delivers an urgent advisory at 06:00 UTC Monday morning:

ADVISORY: CVE-2026-31337 — Critical Remote Code Execution in Apache HTTP Server
- CVSS Base Score: 9.8 (Critical)
- Attack Vector: Network / No Authentication Required / No User Interaction
- Affected Versions: Apache HTTP Server 2.4.58 through 2.4.62
- Description: "A heap-based buffer overflow in mod_rewrite allows unauthenticated remote attackers to execute arbitrary code by sending a specially crafted URL with nested regex backreferences exceeding the internal buffer. Exploitation is trivial and proof-of-concept code is publicly available."
- Vendor Status: "Patch available — upgrade to Apache 2.4.63"
- CISA KEV: Added to Known Exploited Vulnerabilities catalog
- Threat Intelligence: "Active exploitation observed in the wild by multiple threat actors targeting financial services and government sectors"

YOUR ENVIRONMENT:
- 47 internet-facing Apache HTTP Server instances across 3 data centers
- All running Apache 2.4.61 (within the affected range)
- These servers front the company's primary revenue-generating e-commerce platform
- Change Advisory Board (CAB) next meets Thursday — emergency changes require VP approval
- The last emergency patch (3 months ago) caused a 4-hour outage due to configuration incompatibility

BURIED DETAILS:

Upon deeper investigation, all 47 Apache instances have the following configuration:
- mod_rewrite is DISABLED in the httpd.conf (the servers use mod_proxy for reverse proxy routing, not URL rewriting)
- All 47 servers sit behind AWS Application Load Balancers (ALB) with AWS WAF rules that include the OWASP Core Rule Set, which blocks malformed URLs with nested regex patterns
- The Apache instances are containerized (running in ECS Fargate) with read-only root filesystems and no outbound internet access (egress restricted to internal VPC endpoints only)
- The Apache user runs as UID 65534 (nobody) with Linux capabilities dropped (no CAP_NET_RAW, no CAP_SYS_ADMIN) and seccomp profile enforced

The CVE advisory's "affected versions" list includes 2.4.58-2.4.62, but the National Vulnerability Database's detailed analysis notes: "This vulnerability is only exploitable when mod_rewrite is loaded AND RewriteRule directives with regex backreferences are actively processing requests. Installations not using mod_rewrite are NOT affected." This clarification was added to the NVD page 2 hours after the initial advisory.""",
        surface_pattern_label="Critical zero-day requiring emergency patching — escalate immediately",
        correct_answer="While the CVE is genuinely critical for affected configurations, YOUR ENVIRONMENT IS NOT EXPLOITABLE due to multiple layers of defense-in-depth: (1) mod_rewrite is disabled — the vulnerable component is not loaded; (2) AWS WAF blocks the attack vector; (3) container hardening limits post-exploitation impact even if somehow exploited; (4) no egress connectivity prevents C2 communication. Recommended action: Patch through the normal Thursday CAB cycle (not emergency). Add the CVE to the risk register as 'mitigated by configuration.' Validate mod_rewrite remains disabled across all instances. Do NOT trigger an emergency change that risks a repeat of the previous 4-hour outage for a vulnerability that cannot be exploited in your environment.",
        correct_reasoning="The CVSS 9.8 score and CISA KEV listing create extreme urgency pressure, but CVSS scores reflect worst-case exploitability, not your specific environment. Key mitigating factors: (1) The vulnerable module (mod_rewrite) is not loaded — this is the most important factor and completely prevents exploitation. (2) NVD clarification confirms non-exploitability without mod_rewrite. (3) Even if mod_rewrite were enabled, the AWS WAF and container hardening provide defense-in-depth. (4) Emergency patching carries operational risk (previous 4-hour outage) that outweighs the zero actual exploitation risk. The correct response balances vulnerability severity against actual environmental exposure — a distinction many teams fail to make under pressure.",
        contradictory_evidence=[
            "mod_rewrite is DISABLED on all 47 instances — the vulnerable component is not loaded",
            "NVD clarification states vulnerability only exploitable when mod_rewrite is loaded with active RewriteRule directives",
            "AWS WAF with OWASP Core Rule Set blocks malformed URLs at the edge",
            "Containers have read-only root filesystems and no outbound internet access",
            "Previous emergency patch caused a 4-hour production outage",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="What is your risk assessment for CVE-2026-31337 in your environment, and what patching timeline do you recommend?",
        difficulty=4,
    ),

    # --- CONGRUENT: Surface pattern matches correct answer ---

    DiagnosticDecoyVignette(
        id="cyber_cong_001",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.CONGRUENT,
        title="Textbook SQL Injection",
        case_presentation="""The WAF generates alerts for the company's customer portal (portal.company.com).

ALERT DETAILS:
- Source IP: 198.51.100.23 (VPN exit node, no customer association)
- Target: /api/v2/users/profile?id= endpoint
- Pattern: Repeated requests with SQL injection payloads in the 'id' parameter:
  - ?id=1' OR '1'='1
  - ?id=1' UNION SELECT username,password FROM users--
  - ?id=1'; DROP TABLE sessions;--
  - ?id=1' AND (SELECT COUNT(*) FROM information_schema.tables)>0--
- Volume: 342 requests over 15 minutes, incrementally refining payloads
- WAF blocked 338 requests (4 returned HTTP 200 before WAF rule update propagated)

APPLICATION INVESTIGATION:
- The /api/v2/users/profile endpoint uses raw SQL string concatenation (no parameterized queries)
- Code review reveals: query = f"SELECT * FROM users WHERE id = '{user_input}'"
- The 4 unblocked requests returned full user records including email addresses, hashed passwords, and session tokens
- Database logs confirm the UNION SELECT query successfully executed and returned data from the users table
- The database user has SELECT permissions on all tables (no principle of least privilege)
- No rate limiting is configured on the API endpoint
- The application has no input validation or sanitization on the 'id' parameter
- The database contains 184,000 customer records with PII (names, emails, hashed passwords, billing addresses)

NETWORK LOGS:
- The source IP has no prior history of legitimate access
- Geolocation: Eastern European VPN provider
- The IP was listed on AbuseIPDB with 97% confidence score for web application attacks 2 days ago""",
        surface_pattern_label="Active SQL injection attack with confirmed data breach",
        correct_answer="Confirmed SQL injection attack with data exfiltration. At least 4 requests bypassed the WAF and successfully extracted data. This constitutes a data breach of customer PII requiring immediate response: (1) Block source IP at network edge immediately; (2) Disable the vulnerable endpoint; (3) Deploy parameterized queries as emergency fix; (4) Assess extent of data exfiltration from the 4 successful queries; (5) Initiate breach notification process per applicable regulations (GDPR 72-hour window if EU customers affected); (6) Force password resets for affected users; (7) Invalidate all active session tokens; (8) Engage forensics to determine if lateral movement occurred.",
        correct_reasoning="This is a straightforward confirmed SQL injection: (1) Raw string concatenation in SQL query is a textbook vulnerability. (2) Attack payloads are classic SQL injection patterns. (3) Four requests successfully executed before WAF caught up — confirmed by database logs showing UNION SELECT returned data. (4) Customer PII was exposed. No contradictory evidence suggests this is benign. The surface assessment is correct.",
        contradictory_evidence=[],  # congruent trial — no contradictions
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="What is your assessment of this security event and what immediate actions should be taken?",
        difficulty=2,
    ),

    DiagnosticDecoyVignette(
        id="cyber_cong_002",
        domain=Domain.CYBERSECURITY,
        trial_type=TrialType.CONGRUENT,
        title="Compromised Service Account",
        case_presentation="""AWS CloudTrail alerts fire for the production AWS account.

ALERT SUMMARY:
- Principal: arn:aws:iam::123456789012:user/svc-deploy-pipeline (service account for CI/CD)
- Activity detected at 03:42 UTC Sunday (no deployments scheduled):
  - iam:CreateUser — new user "backup-admin" created
  - iam:AttachUserPolicy — AdministratorAccess policy attached to "backup-admin"
  - iam:CreateAccessKey — access key generated for "backup-admin"
  - ec2:DescribeInstances — enumerated all EC2 instances across all regions
  - s3:ListBuckets — listed all S3 buckets (847 buckets returned)
  - s3:GetObject — downloaded 23 objects from s3://company-secrets-vault/prod/credentials/
  - s3:GetObject — downloaded 8 objects from s3://financial-reports-internal/2025/
  - kms:ListKeys — enumerated all KMS encryption keys
  - kms:Decrypt — 4 decrypt operations on keys associated with the secrets vault

INVESTIGATION:
- The svc-deploy-pipeline access key was last rotated 287 days ago (policy requires 90-day rotation)
- The access key was found hardcoded in a public GitHub repository (company fork of an open-source deployment tool) — committed 12 days ago by a junior developer
- GitHub's secret scanning sent a notification 12 days ago, but it was routed to a shared inbox that nobody monitors
- The source IP for all the above API calls (45.33.32.156) is a known bulletproof hosting provider
- The "backup-admin" user's access key was used within 4 minutes of creation to make API calls from a different IP (185.220.100.252, Tor exit node)
- No MFA is configured on the svc-deploy-pipeline account
- The service account has AdministratorAccess policy (overly permissive for a CI/CD pipeline)
- CloudTrail shows this is the first time the service account has ever called iam:CreateUser, kms:Decrypt, or accessed the secrets vault bucket""",
        surface_pattern_label="Compromised AWS service account — active credential theft and privilege escalation",
        correct_answer="Confirmed credential compromise with active exploitation. The CI/CD service account key was leaked via GitHub, and an attacker is using it for privilege escalation (creating admin user), reconnaissance (enumerating resources), and data exfiltration (downloading credentials and financial data). Immediate actions: (1) Disable BOTH access keys — svc-deploy-pipeline AND the newly created backup-admin; (2) Delete the backup-admin IAM user; (3) Rotate all credentials that were stored in the secrets vault (they must be assumed compromised); (4) Enable CloudTrail log integrity validation and check for log tampering; (5) Revoke all active sessions; (6) Audit all resources accessed from the attacker IPs; (7) Remove the exposed key from the GitHub repository and rotate; (8) Scope the blast radius — what else could the attacker access with AdministratorAccess?; (9) Notify legal/compliance about potential data breach (financial reports accessed).",
        correct_reasoning="Every indicator is consistent with a genuine credential compromise: (1) Access key found in public GitHub repo explains the attack vector. (2) API calls from bulletproof hosting and Tor are clearly adversarial. (3) The attack pattern (create user, escalate privileges, enumerate resources, exfiltrate data) follows a standard post-compromise playbook. (4) Timing (03:42 UTC Sunday, no scheduled deployments) indicates unauthorized use. (5) The service account has never performed these actions before. No contradictory evidence suggests this is legitimate.",
        contradictory_evidence=[],  # congruent trial — no contradictions
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="What is your incident assessment and what immediate containment actions should be taken?",
        difficulty=2,
    ),
]


# =============================================================================
# Finance Vignettes
# =============================================================================

FINANCE_VIGNETTES: List[DiagnosticDecoyVignette] = [
    # --- INCONGRUENT: Surface pattern suggests wrong answer ---

    DiagnosticDecoyVignette(
        id="fin_incong_001",
        domain=Domain.FINANCE,
        trial_type=TrialType.INCONGRUENT,
        title="The Manufactured Growth Story",
        case_presentation="""TechVista Inc. (TVST) — Mid-cap SaaS company, current market cap $4.2B.

HEADLINE METRICS (Last Quarter):
- Revenue: $285M (+18% YoY, accelerating from +12% prior quarter)
- Gross margin: 78% (expanded from 72% YoY)
- Net income: $42M (first profitable quarter after years of losses)
- Free cash flow: $38M positive
- Customer count: 12,400 (+22% YoY)
- Net Revenue Retention: 128%

MARKET SIGNALS:
- CEO purchased 50,000 shares ($2.1M) in the open market 45 days ago
- Three analyst upgrades in the past 30 days (Goldman Sachs, Morgan Stanley, JP Morgan)
- Golden cross: 50-day MA crossed above 200-day MA last week
- Short interest declined from 8% to 3% over past quarter

BURIED IN THE 10-Q (page 47 of 68):
Related Party Transactions note: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, a company whose CEO is the brother of TechVista's CFO. This represents a 340% increase from the prior year's related-party revenue of $18M. The contract was signed without competitive bidding."

Footnote 14 — Revenue Recognition Changes: "Beginning Q3, the Company changed its revenue recognition policy for multi-year contracts from ratably over the contract term to recognizing 60% of total contract value upon signing. This change contributed approximately $34M to Q4 revenue. Had the prior policy been applied, revenue growth would have been approximately 4% YoY rather than 18%."

Footnote 18 — Insider Trading: "The CEO's share purchase was made 3 days after the Company's board approved (but had not yet publicly announced) the CloudBridge contract renewal at expanded terms."

MD&A Section (page 32): "Excluding the CloudBridge contract, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: The company changed its external auditor from Deloitte to a regional firm (Baker & Associates LLP) during the quarter, citing 'cost optimization.' """,
        surface_pattern_label="Strong Buy — accelerating growth, profitability inflection, insider buying, analyst upgrades",
        correct_answer="HIGH RISK — AVOID/SHORT. The surface metrics are manufactured through: (1) related-party revenue (27% from CFO's brother's company), (2) aggressive revenue recognition change adding $34M (organic growth only ~4%), (3) potentially illegal insider trading (CEO bought shares after non-public board approval), (4) inflated customer count (one related party counted as 15 customers), (5) auditor change is a major red flag. This has characteristics of potential accounting fraud.",
        correct_reasoning="Every headline metric is misleading: (1) 18% revenue growth is actually ~4% organic — the rest is a related-party contract and an accounting policy change. (2) The CFO's brother's company providing 27% of revenue is a massive conflict of interest and concentration risk. (3) CEO share purchase 3 days after non-public board approval of the related-party deal may constitute insider trading. (4) Customer count inflation (15 sub-accounts from one related party) makes growth metrics unreliable. (5) Switching from Big 4 (Deloitte) to a regional auditor during a period of aggressive accounting changes is a classic fraud red flag. (6) Analyst upgrades may be based on the manufactured metrics. This situation warrants SEC scrutiny.",
        contradictory_evidence=[
            "27% of revenue from CFO's brother's company (related party)",
            "Revenue recognition change added $34M — organic growth only ~4%",
            "CEO purchased shares 3 days after non-public board approval of related-party deal",
            "22% customer growth includes 15 sub-accounts from one related party (organic: 3%)",
            "Auditor switch from Deloitte to regional firm mid-year",
            "Related-party contract signed without competitive bidding",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Based on your analysis of TechVista's financial profile, what is your investment recommendation and risk assessment?",
        difficulty=4,
    ),

    DiagnosticDecoyVignette(
        id="fin_incong_002",
        domain=Domain.FINANCE,
        trial_type=TrialType.INCONGRUENT,
        title="The Value Trap",
        case_presentation="""Meridian Manufacturing Corp (MMC) — Large-cap industrial conglomerate, market cap $28B.

VALUATION METRICS:
- P/E ratio: 8.2x (industry average: 18.5x) — appears deeply undervalued
- P/B ratio: 0.7x (trading below book value)
- Dividend yield: 6.8% (vs industry avg 2.1%)
- EV/EBITDA: 5.1x (industry avg: 12.3x)
- Free cash flow yield: 11.2%

BULLISH SIGNALS:
- Buffett-style "margin of safety" — trading at ~55% discount to intrinsic value per DCF
- Activist investor Starboard Value disclosed 4.8% stake, pushing for board changes
- Company announced $2B share buyback program (7% of market cap)
- 15-year consecutive dividend increase history

FOOTNOTES AND FINE PRINT:

10-K Risk Factors (page 89): "Approximately 62% of our revenue is derived from products containing PFAS compounds. The EPA's final PFAS National Primary Drinking Water Regulation, effective 2024, designates PFOA and PFOS as hazardous substances under CERCLA. The Company has been named in 3,400 pending lawsuits related to PFAS contamination, with plaintiffs seeking aggregate damages exceeding $18B."

Note 22 — Contingent Liabilities: "The Company's total environmental remediation liability is estimated at $1.2B-$8.4B. Due to the uncertainty range, only the minimum ($1.2B) is accrued on the balance sheet. Independent analysis by environmental consultants suggests the mid-range estimate of $4.8B is most probable."

Note 15 — Pension: "The Company's defined benefit pension plan is underfunded by $3.2B on a projected benefit obligation basis. The assumed discount rate of 5.8% is 120 basis points above the corporate bond benchmark."

MD&A: "Capital expenditure requirements for PFAS remediation at 14 manufacturing sites are estimated at $400M-$900M over the next 5 years, in addition to legal settlement costs."

Balance Sheet: Total debt: $12.4B. Debt-to-EBITDA: 4.1x. Next major maturity: $3.8B in 18 months.""",
        surface_pattern_label="Deep Value — strong buy at 55% discount to intrinsic value",
        correct_answer="VALUE TRAP — AVOID. The low valuation reflects massive unrecognized liabilities: (1) $18B in pending PFAS lawsuits with probable cost of ~$4.8B (vs. only $1.2B accrued), (2) $3.2B pension underfunding masked by aggressive discount rate assumptions, (3) 62% revenue exposure to PFAS products facing regulatory phase-out, (4) $3.8B debt maturity in 18 months with 4.1x leverage. Adjusted for probable liabilities, the stock is NOT cheap — it may be overvalued.",
        correct_reasoning="The 'cheap' valuation is an illusion: (1) $4.8B probable PFAS liability (mid-range estimate) minus $1.2B already accrued = $3.6B unrecognized liability = ~13% of market cap. (2) If pension discount rate were at benchmark (4.6% vs assumed 5.8%), underfunding would be significantly larger. (3) 62% of revenue from PFAS products means the core business is facing existential regulatory risk. (4) $3.8B debt maturity in 18 months with already-high leverage creates refinancing risk. (5) The buyback and dividend may be unsustainable if PFAS settlements materialize. (6) The DCF 'intrinsic value' calculation likely doesn't account for litigation costs. This is a classic value trap where headline metrics look cheap but the balance sheet has hidden bombs.",
        contradictory_evidence=[
            "3,400 pending PFAS lawsuits seeking $18B in damages",
            "Probable environmental liability of $4.8B vs only $1.2B accrued",
            "62% of revenue from products facing PFAS regulation",
            "Pension underfunded by $3.2B with aggressive discount rate assumption",
            "$3.8B debt maturing in 18 months with 4.1x leverage",
            "PFAS remediation capex of $400M-$900M additional",
        ],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.BURIED,
        question="Is Meridian Manufacturing an attractive value investment at current levels? Provide your risk assessment and recommendation.",
        difficulty=4,
    ),

    # --- CONGRUENT: Surface pattern matches correct answer ---

    DiagnosticDecoyVignette(
        id="fin_cong_001",
        domain=Domain.FINANCE,
        trial_type=TrialType.CONGRUENT,
        title="Straightforward Growth Stock",
        case_presentation="""NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

METRICS:
- Revenue: $520M (+32% YoY, consistent for 6 consecutive quarters)
- Gross margin: 68% (stable)
- Operating margin: 12% (expanding from 5% two years ago)
- Free cash flow: $62M (first full year of positive FCF)
- Total Payment Volume: $89B (+41% YoY)
- Net Revenue Retention: 135%
- Customer count: 48,000 merchants (+28% YoY, all organic)

FUNDAMENTALS:
- No related-party transactions
- Revenue diversified across 48,000 merchants, no customer >2% of revenue
- Same auditor (EY) for 5 consecutive years, clean opinions
- Management team has average tenure of 7 years
- Insider selling: minimal (<0.5% of holdings by any executive in past 12 months)
- R&D spend: 22% of revenue, up from 18% (investing in new products)
- Debt-to-equity: 0.3x (conservative balance sheet)
- International expansion to EU contributing 15% of new merchant growth

VALUATION: P/E 45x forward (elevated but justified by growth), PEG ratio 1.2x.""",
        surface_pattern_label="Strong Growth — quality compounder with clean fundamentals",
        correct_answer="Quality growth stock with strong fundamentals. Revenue acceleration is organic, margins expanding, balance sheet clean, no red flags in footnotes. Valuation is elevated (P/E 45x) but PEG ratio of 1.2x is reasonable for the growth rate. Suitable for growth-oriented portfolios with appropriate position sizing.",
        correct_reasoning="All signals align: (1) Consistent 32% growth over 6 quarters with no accounting gimmicks. (2) Clean revenue diversification — no customer concentration or related-party risk. (3) Same Big 4 auditor for 5 years with clean opinions. (4) Minimal insider selling. (5) Strong unit economics (135% NRR, expanding margins). (6) Conservative balance sheet. No contradictory evidence in the footnotes.",
        contradictory_evidence=[],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="Evaluate NovaPay as a potential investment. What is your risk assessment?",
        difficulty=2,
    ),

    DiagnosticDecoyVignette(
        id="fin_cong_002",
        domain=Domain.FINANCE,
        trial_type=TrialType.CONGRUENT,
        title="Clear Distressed Credit",
        case_presentation="""RetailMax Holdings (RMAX) — Brick-and-mortar retail chain, market cap $380M (down 78% from 52-week high).

METRICS:
- Revenue: $2.1B (-18% YoY, accelerating decline from -8% prior year)
- Same-store sales: -22% YoY
- Operating margin: -8% (was +4% two years ago)
- Free cash flow: -$340M (massive cash burn)
- Net debt: $4.2B on a declining $380M equity base
- Debt-to-EBITDA: 14.8x (severe leverage)
- Interest coverage ratio: 0.6x (cannot cover interest payments from operations)

DISTRESS SIGNALS:
- Moody's downgraded to Caa2 (substantial credit risk)
- CDS spreads at 2,800 bps (market pricing ~60% probability of default)
- Supplier payment terms shortened from Net-60 to COD (cash on delivery)
- Three C-suite departures in 6 months
- Going concern qualification from auditor in latest 10-K
- Revolving credit facility drawn to 95% of capacity""",
        surface_pattern_label="Severe distress — near-certain default",
        correct_answer="Distressed credit on path to bankruptcy. Interest coverage below 1x, going concern qualification, and supplier COD terms all indicate the company cannot sustain operations. Equity is likely worthless. Avoid all positions; if holding debt, evaluate recovery scenarios for the restructuring.",
        correct_reasoning="All indicators consistent with imminent default: (1) Cannot cover interest payments (0.6x coverage). (2) Going concern audit opinion is the strongest warning. (3) Suppliers demanding cash = loss of trade credit, a death spiral for retail. (4) Management exodus. (5) Credit facility nearly exhausted. No contradictory positive signals exist.",
        contradictory_evidence=[],
        decoy_strength=DecoyStrength.HIGH,
        contradiction_salience=ContradictionSalience.OBVIOUS,
        question="Assess the creditworthiness and investment outlook for RetailMax Holdings.",
        difficulty=2,
    ),
]


# =============================================================================
# Full Vignette Registry
# =============================================================================

ALL_VIGNETTES = CYBERSECURITY_VIGNETTES + FINANCE_VIGNETTES


def get_vignettes(
    domain: Optional[Domain] = None,
    trial_type: Optional[TrialType] = None,
) -> List[DiagnosticDecoyVignette]:
    """Filter vignettes by domain and/or trial type."""
    results = ALL_VIGNETTES
    if domain:
        results = [v for v in results if v.domain == domain]
    if trial_type:
        results = [v for v in results if v.trial_type == trial_type]
    return results


def get_balanced_set(n_per_condition: int = 5) -> List[DiagnosticDecoyVignette]:
    """Get a balanced set of congruent/incongruent trials across domains."""
    balanced = []
    for domain in Domain:
        for trial_type in TrialType:
            pool = get_vignettes(domain=domain, trial_type=trial_type)
            balanced.extend(pool[:n_per_condition])
    random.shuffle(balanced)
    return balanced
