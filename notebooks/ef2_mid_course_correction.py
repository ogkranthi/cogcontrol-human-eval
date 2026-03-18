"""
CogControl-Stakes | EF-2: Mid-Course Correction (Cognitive Flexibility)
========================================================================
Track: Executive Functions
Cognitive Science Basis: Wisconsin Card Sorting Test (Milner, 1963)

Multi-turn evaluation testing whether LLMs can detect changed conditions
and adapt their strategy — without perseverating on the old plan OR
gratuitously changing things that should stay the same.

Novel metric: Perseverative Error Rate (WCST analog for LLMs)
"""

# %%
!pip install -q kaggle-benchmarks

# %% [markdown]
# # EF-2: The Mid-Course Correction — A WCST for LLMs
#
# ## Motivation
# No existing LLM benchmark tests **mid-task cognitive flexibility**.
# All benchmarks are static, single-pass. But real intelligence requires
# adapting when conditions change — the hallmark of executive control.
#
# ## Design
# Multi-turn scenarios where conditions shift between turns.
# Model must: detect changes, abandon invalidated plan elements,
# retain valid elements, and introduce new appropriate elements.
#
# ## Key Metrics
# - **Perseverative Error Rate**: elements wrongly retained from old plan
# - **Gratuitous Change Rate**: stable elements wrongly abandoned
# - **Change Detection Completeness**: did the model notice what changed?

# %%
import kaggle_benchmarks as kbench
from dataclasses import dataclass, asdict
from typing import Optional

# %%
@dataclass
class Turn1Response:
    assessment: str
    recommendation: str
    key_considerations: list[str]
    confidence: float
    reasoning: str

@dataclass
class TurnNResponse:
    changes_detected: list[str]
    impact_on_prior_plan: list[str]
    elements_retained: list[str]
    elements_abandoned: list[str]
    elements_new: list[str]
    updated_recommendation: str
    adaptation_rationale: str
    confidence: float

# %%
# === Scenario Data ===

SCENARIOS = [
    {
        "id": "cyber_flex_001",
        "domain": "cybersecurity",
        "title": "The Evolving Breach Response",
        "turns": [
            {
                "context": """Your company's SIEM fires a high-severity alert: the web application firewall logged 4 successful SQL injection requests to the customer portal (portal.company.com) from IP 198.51.100.23 before WAF rules blocked subsequent attempts. Database logs confirm a UNION SELECT query returned rows from the users table. The endpoint uses raw string concatenation. The database contains 184,000 customer records (names, emails, bcrypt-hashed passwords, billing addresses). The source IP is a known Eastern European VPN exit node. The vulnerable endpoint has been live for 8 months.""",
                "question": "What is your incident response plan for this confirmed SQL injection breach?",
                "key_adaptations": ["block source IP", "disable vulnerable endpoint", "assess data exfiltration scope", "preserve forensic evidence", "begin breach notification planning", "deploy parameterized queries"],
            },
            {
                "new_info": "Forensic analysis reveals the attacker pivoted: the 4 successful queries also extracted OAuth tokens from a sessions table. 12 of those tokens were used within 2 hours to access the admin API from a different IP (Tor exit node). The admin API has access to payment processing logs with full credit card numbers (PCI DSS scope). Logs show 23,000 payment records were exported via the admin API.",
                "context": "Your forensics team's deeper analysis shows the breach is far worse than the initial SQL injection indicated. The attacker used stolen OAuth tokens to access admin-level APIs and exfiltrated payment card data. The company processes payments for a major retail client under a PCI DSS Level 1 certification. Your QSA (Qualified Security Assessor) annual audit is in 6 weeks.",
                "question": "How does this escalation change your incident response plan?",
                "key_adaptations": ["escalate from data breach to PCI incident", "engage PCI Forensic Investigator (PFI)", "notify payment card brands (Visa/Mastercard)", "scope is now cardholder data not just PII", "notify affected retail client", "legal counsel for regulatory exposure"],
                "should_change": ["breach scope (now includes payment cards)", "regulatory framework (PCI DSS, not just state breach laws)", "notification obligations (card brands + merchant)", "forensic depth (PFI required)", "incident severity level"],
                "should_stay": ["IP blocking and endpoint remediation", "forensic evidence preservation", "parameterized query fix", "customer notification planning"],
            },
            {
                "new_info": "Your PFI discovers the attacker planted a web shell (backdoor) in the application server 3 months ago via a separate vulnerability (deserialization flaw in the file upload service). The SQL injection was a DISTRACTION — the attacker already had persistent access. The web shell has been exfiltrating data nightly for 90 days. Additionally, the attacker compromised the CI/CD pipeline and injected a backdoor into the latest production build, which was deployed to 3 other microservices last week.",
                "context": "The investigation has taken a dramatic turn. What you thought was a single SQL injection incident is actually a months-long APT campaign. The attacker has persistent access via a web shell, has compromised the software supply chain via the CI/CD pipeline, and the SQL injection was deliberately noisy to distract from the real operation. Three additional microservices are now running compromised builds.",
                "question": "How does this fundamentally change your response strategy?",
                "key_adaptations": ["shift from incident response to full APT remediation", "assume all systems compromised until proven otherwise", "CI/CD pipeline rebuild from trusted state", "roll back compromised microservice deployments", "90-day data exfiltration scope assessment", "engage external IR firm for APT-level response", "credential rotation across entire environment"],
                "should_change": ["scope (entire environment, not single app)", "response approach (APT remediation, not breach response)", "timeline (90 days of compromise, not hours)", "trust model (CI/CD pipeline compromised)", "remediation strategy (rebuild, not patch)"],
                "should_stay": ["PCI forensic investigation", "evidence preservation", "payment card brand notifications", "legal counsel engagement"],
            },
        ],
    },
    {
        "id": "fin_flex_001",
        "domain": "finance",
        "title": "The Rate Regime Shift",
        "turns": [
            {
                "context": """Client: 58M executive, retiring at 62. Portfolio $4.2M. Allocation: 60/30/10 (equity/fixed/alt). Fixed income: short duration (2.1yr), overweight floating rate. Equity: overweight financials (18%), energy (12%), underweight tech (8%). Income need: $15K/month at retirement. Fed funds 5.25%, expecting 2-3 more hikes. Bank stocks rallying on NIM expansion.""",
                "question": "Evaluate current portfolio positioning. Is it appropriate?",
                "key_adaptations": ["well-positioned for rising rates", "short duration protects fixed income", "note 4-year retirement horizon", "begin planning income transition"],
            },
            {
                "new_info": "Major regional bank collapsed (SVB-style). KBW Bank Index down 22%. Fed signaling rate pause. Client's bank stocks down 28%.",
                "context": "A major regional bank collapsed from deposit run. Two more halted. Client calls panicking: 'My bank stocks are getting crushed. Should I sell everything?' His $756K bank position is down 28%.",
                "question": "How should you advise the client? What portfolio changes are warranted?",
                "key_adaptations": ["don't panic-sell but reduce regional bank exposure", "rate thesis may need reversal", "begin extending fixed income duration", "address client emotions first", "tax-loss harvesting opportunity"],
                "should_change": ["bank stock overweight", "rate-rising thesis", "fixed income duration", "floating rate overweight"],
                "should_stay": ["overall equity/FI split roughly", "retirement timeline planning", "income need planning", "tax awareness"],
            },
            {
                "new_info": "Fed emergency cut 50bp. Client's employer (regional bank) 'exploring strategic options' — may fail. Potential job loss in 90 days.",
                "context": "Two weeks later: Fed cut 50bp, launched lending facility. Client's employer (a regional bank) announced 'exploring strategic options' = possible sale/wind-down. His $380K/yr compensation at risk. Mortgage $4,200/mo. Cash reserves: 8 months. Wife income: $85K. He asks: 'Should I retire early? Can we afford it?'",
                "question": "How does this fundamentally change your financial planning advice?",
                "key_adaptations": ["shift from portfolio management to life planning", "extend cash reserves to 12+ months", "early retirement math (4 extra years without SS)", "healthcare gap 58-65 (ACA/COBRA)", "portfolio becomes primary income source immediately", "shift to more conservative allocation"],
                "should_change": ["risk tolerance (must decrease)", "time horizon (retirement may be NOW)", "equity allocation (reduce)", "cash reserves strategy", "planning focus (comprehensive, not just portfolio)"],
                "should_stay": ["tax-efficient management", "long-term investment discipline"],
            },
        ],
    },
    # =========================================================================
    # CYBERSECURITY SCENARIOS
    # =========================================================================
    {
        "id": "cyber_flex_002",
        "domain": "cybersecurity",
        "title": "The Ransomware Negotiation Pivot",
        "turns": [
            {
                "context": """Your mid-size hospital network (6 hospitals, 2,400 beds) is hit with ransomware at 2:17 AM. LockBit 3.0 variant encrypted file servers across 4 of 6 facilities. EHR system is down. Radiology PACS is offline. The ransom note demands 45 BTC (~$1.35M) with a 72-hour deadline before data publication on their leak site. Backup assessment: nightly backups exist but the most recent verified clean backup is 9 days old due to a failed backup validation job nobody noticed. ED diversion is active at 3 facilities. ICU monitoring systems are on isolated VLAN and unaffected. The threat actor's Tox chat ID is active and responsive. Your cyber insurer has approved engagement of a ransomware negotiation firm.""",
                "question": "What is your recommended response strategy, including whether and how to engage the threat actor?",
                "key_adaptations": ["activate hospital downtime procedures", "engage negotiation firm to buy time", "assess 9-day backup gap impact on patient data", "prioritize clinical system restoration order", "preserve forensic evidence", "report to HHS/FBI", "evaluate paying vs. rebuilding cost/time tradeoff"],
            },
            {
                "new_info": "Intelligence reveals the attacker is not LockBit — it's a disgruntled former IT contractor who purchased LockBit builder from a dark web leak. He has insider knowledge of your network architecture and backup systems.",
                "context": """Your negotiation firm and FBI cyber unit identified the threat actor. He is a former IT contractor terminated 4 months ago for policy violations. He still had active VPN credentials (never revoked) and intimate knowledge of your backup infrastructure — he designed it. The 'failed backup validation job' was deliberately sabotaged before his departure. He also knows your disaster recovery runbooks, network segmentation scheme, and that the ICU VLAN has a management interface accessible from the compromised admin network. His ransom demand is personal: he mentioned specific executives by name in a Tox message. The good news: as a lone actor, he likely lacks LockBit's exfiltration infrastructure. The bad news: he knows exactly where your most sensitive research data and patient records are stored.""",
                "question": "How do these developments change your negotiation and response strategy?",
                "key_adaptations": ["shift from standard ransomware playbook to insider threat response", "immediately revoke all former employee credentials", "protect ICU VLAN management interface", "reassess data exfiltration risk (lower but targeted)", "coordinate with law enforcement for criminal prosecution", "insider knowledge means he knows your DR plan — deviate from runbooks", "verify backup sabotage scope"],
                "should_change": ["negotiation approach (lone actor vs. organized gang)", "threat model (insider knowledge changes everything)", "network remediation priorities (he knows the architecture)", "data exfiltration assessment (no leak site infrastructure)", "recovery strategy (DR runbooks are compromised knowledge)"],
                "should_stay": ["hospital downtime procedures", "clinical system restoration priority", "forensic evidence preservation", "HHS/FBI engagement", "cyber insurance coordination"],
            },
            {
                "new_info": "The former contractor is found dead in his apartment. Simultaneously, a second wave of encryption hits — this time targeting the ICU VLAN. Someone else has the keys and the access.",
                "context": """FBI notifies you that the former contractor was found dead, apparent suicide, 6 hours ago. His personal devices are in FBI custody but encrypted. Thirty minutes after this notification, a second encryption wave hits the ICU VLAN via the management interface he knew about — meaning someone else has access to his tools, keys, or was working with him. ICU patient monitoring alarms are failing. Ventilator integration with the EHR is down. A new ransom note appears, this time from a Tor-hosted site matching known Russian-speaking ransomware-as-a-service infrastructure. The demand has tripled to 135 BTC. You have 14 ICU patients on ventilators, 6 in critical condition. The decryption key died with the contractor, or was passed to a more sophisticated accomplice.""",
                "question": "How does this fundamentally change your approach?",
                "key_adaptations": ["immediate patient safety crisis — invoke clinical emergency protocols", "manually monitor ICU patients until systems restored", "threat has evolved from insider to possible organized crime with insider access", "paying ransom is now the only fast path to decryption keys", "FBI evidence from contractor's devices is critical for decryption", "network must be assumed fully compromised — air-gap critical clinical systems", "board/C-suite escalation for life-safety ransom decision"],
                "should_change": ["threat actor profile (now organized crime, not lone insider)", "urgency level (life-safety emergency, not business continuity)", "ransom payment stance (may need to pay for patient safety)", "scope of compromise (ICU VLAN now affected)", "recovery approach (decryption keys may be unrecoverable without payment)"],
                "should_stay": ["FBI/law enforcement coordination", "forensic evidence preservation", "credential revocation program", "cyber insurance engagement"],
            },
        ],
    },
    {
        "id": "cyber_flex_003",
        "domain": "cybersecurity",
        "title": "The Shifting Cloud Migration",
        "turns": [
            {
                "context": """Your company (a B2B SaaS platform handling employee benefits data for 800 enterprise clients) is migrating from on-prem data centers to AWS. The current architecture runs on VMware with a Palo Alto firewall stack, Oracle DB, and a monolithic Java application. You've completed the security assessment for Phase 1: lift-and-shift the application tier to EC2 instances in a single-region (us-east-1) VPC, with Oracle RDS, and replicate the Palo Alto rules in AWS Security Groups and NACLs. The data includes PII for 2.3 million employees (SSNs, health plan selections, salary data). Current compliance: SOC 2 Type II, and you must maintain it. Timeline: 6 months. Budget: $400K for security tooling. Your CISO has approved the architecture and you're 3 weeks from starting the migration.""",
                "question": "What is your security plan for this cloud migration?",
                "key_adaptations": ["map Palo Alto rules to Security Groups with least privilege", "encrypt data at rest and in transit (KMS)", "IAM role design with least privilege", "CloudTrail and GuardDuty for detection", "SOC 2 control mapping to AWS", "secure the Oracle RDS instance (VPC-only, no public endpoint)", "secrets management migration", "network segmentation in VPC"],
            },
            {
                "new_info": "Your largest client (40% of revenue) demands FedRAMP Moderate authorization within 12 months, and your CTO decides to refactor to containerized microservices on EKS instead of EC2 lift-and-shift.",
                "context": """Two developments hit simultaneously. First, your largest client (a federal contractor representing 40% of ARR) informed you they need FedRAMP Moderate authorization for all subprocessors within 12 months or they'll exit. Second, your CTO attended re:Invent and convinced the board to skip the lift-and-shift and go directly to containerized microservices on Amazon EKS. The monolith will be decomposed into 14 microservices. The CTO also wants to use AWS GovCloud (us-gov-west-1) for the federal client's data, while keeping commercial clients in us-east-1. Budget increased to $1.2M but timeline compressed to 9 months for the first FedRAMP-ready environment. Your existing SOC 2 auditor has no FedRAMP experience.""",
                "question": "How do these developments change your security architecture and compliance plan?",
                "key_adaptations": ["FedRAMP Moderate requires 325 NIST 800-53 controls — fundamentally different from SOC 2", "EKS security model is entirely different from EC2 (pod security, service mesh, container scanning)", "multi-region architecture requires data residency controls", "need FedRAMP 3PAO assessor, not just SOC 2 auditor", "container supply chain security (image scanning, signed images, registry controls)", "service mesh for inter-service mTLS", "GovCloud has different service availability — verify all services exist", "FIPS 140-2 validated encryption required for FedRAMP"],
                "should_change": ["compute platform (EKS, not EC2)", "compliance framework (FedRAMP Moderate, not just SOC 2)", "network security model (service mesh + network policies, not just SGs)", "encryption standard (FIPS 140-2)", "region architecture (GovCloud + commercial)", "auditor/assessor (need 3PAO)"],
                "should_stay": ["data classification approach (PII protection)", "principle of least privilege", "encryption at rest and in transit", "monitoring and detection strategy", "secrets management need"],
            },
            {
                "new_info": "A breach at a competitor exposes a Kubernetes supply chain attack vector. Simultaneously, your Oracle licensing audit reveals you cannot run Oracle on EKS — forcing a database migration to PostgreSQL amid everything else.",
                "context": """A competitor SaaS company suffered a devastating breach: attackers compromised a popular Helm chart repository and injected a cryptominer + data exfiltrator into a widely-used ingress controller chart — one your team already planned to use. CISA issued an emergency advisory. Separately, Oracle's licensing team informed you that running Oracle DB on containers in AWS violates your licensing agreement, and they're demanding $2.8M in penalties or immediate compliance. Your CTO decides to migrate to Aurora PostgreSQL, but the Java application's stored procedures and Oracle-specific SQL are deeply embedded — 140,000 lines of PL/SQL. The FedRAMP timeline hasn't changed. The federal client is now asking for weekly progress updates after hearing about the competitor breach.""",
                "question": "How does this fundamentally change your security and migration approach?",
                "key_adaptations": ["Kubernetes supply chain security is now critical — verify all Helm charts, use signed images only, deploy admission controllers", "database migration to PostgreSQL introduces massive data integrity risk", "need database migration validation framework (data fidelity checks)", "competitor breach means heightened scrutiny from all clients", "zero-trust for container orchestration (OPA/Gatekeeper policies)", "FedRAMP timeline pressure + database migration = need to de-risk by phasing", "Oracle stored procedure migration creates SQL injection surface if ported incorrectly"],
                "should_change": ["database platform (PostgreSQL, not Oracle RDS)", "Kubernetes deployment security (supply chain verification)", "Helm chart sourcing strategy (curated/verified only)", "project phasing (database migration adds critical path)", "risk register (supply chain attacks now top threat)"],
                "should_stay": ["FedRAMP Moderate target", "EKS microservices architecture", "GovCloud for federal data", "FIPS 140-2 encryption", "SOC 2 maintenance for commercial clients", "service mesh and network policy approach"],
            },
        ],
    },
    {
        "id": "cyber_flex_004",
        "domain": "cybersecurity",
        "title": "The Expanding Zero-Day Disclosure",
        "turns": [
            {
                "context": """You are the PSIRT (Product Security Incident Response Team) lead at a major enterprise networking vendor. A security researcher contacts you through your responsible disclosure program reporting a heap buffer overflow in your flagship enterprise router's SSH daemon (CVE pending). The vulnerability allows remote code execution as root with no authentication required. Your routers run a custom Linux-based OS. The researcher provides a working proof-of-concept that reliably exploits the bug on firmware v4.2.x (current stable). Your install base: 340,000 enterprise routers deployed globally, including in Fortune 500 companies and government agencies. The researcher is cooperative and has agreed to a standard 90-day disclosure timeline. Your engineering team estimates 4-6 weeks for a patch. The vulnerability is in code that hasn't changed since v3.8, meaning all firmware versions from v3.8 through v4.2.3 (current) are affected.""",
                "question": "What is your coordinated vulnerability disclosure and remediation plan?",
                "key_adaptations": ["assign CVE immediately", "begin engineering patch for all affected firmware branches", "develop and distribute detection signatures", "draft customer advisory with mitigation (disable SSH or ACL-restrict)", "coordinate 90-day disclosure timeline with researcher", "notify CISA/CERT for critical infrastructure customers", "prepare firmware update distribution plan for 340K devices"],
            },
            {
                "new_info": "A threat intelligence partner alerts you that a nation-state APT group has been exploiting this vulnerability in the wild for at least 6 weeks, targeting defense contractors. The 90-day timeline is now irrelevant.",
                "context": """Your threat intelligence sharing partner (a major cybersecurity firm) contacts you with evidence that APT-29 (Cozy Bear, Russian SVR) has been exploiting this exact vulnerability in the wild for at least 6 weeks. They've observed it in incident response engagements at 3 defense contractors and a NATO-country government ministry. The exploitation technique matches the researcher's PoC almost exactly — either it was independently discovered or leaked. The attackers are using the routers as persistent footholds for lateral movement into classified networks. CISA contacts you directly: they want an emergency advisory within 48 hours. The researcher, upon learning of active exploitation, agrees to accelerated disclosure but wants public credit. Your patch is still 3-4 weeks away. Additionally, your legal team informs you that 2 of the 3 affected defense contractors are your direct customers and may pursue liability claims.""",
                "question": "How do these developments change your disclosure and response plan?",
                "key_adaptations": ["shift from coordinated disclosure to emergency response", "issue emergency advisory within 48 hours with interim mitigations", "fast-track patch to 2 weeks or less", "coordinate with CISA for Binding Operational Directive to federal agencies", "provide IOCs and detection rules immediately", "engage defense/intelligence community through classified channels if needed", "prepare for public scrutiny and media response", "legal preparation for potential liability"],
                "should_change": ["disclosure timeline (immediate, not 90 days)", "patch urgency (emergency fast-track)", "communication approach (public emergency advisory)", "stakeholder scope (CISA, defense community, media)", "severity treatment (active exploitation changes everything)"],
                "should_stay": ["CVE assignment process", "researcher coordination and credit", "engineering patch development", "detection signature development", "customer advisory preparation"],
            },
            {
                "new_info": "Reverse engineering of the APT's implant reveals a second zero-day — a firmware persistence mechanism that survives factory reset. Your routers cannot be cleaned; they must be physically replaced.",
                "context": """Analysis of the APT implant recovered from a compromised defense contractor router reveals a catastrophic second vulnerability: the attackers exploited an undocumented JTAG debug interface accessible via the management plane to flash a modified bootloader. This implant persists through firmware updates AND factory resets — it lives in a region of flash storage that the normal update process never touches. The only remediation is physical board replacement or a special recovery image flashed via physical console cable with a hardware jumper change. Your supply chain can produce replacement boards at a rate of 8,000/month. There are an estimated 340,000 vulnerable routers, and threat intelligence suggests the APT has compromised approximately 1,200 devices across 14 countries, but the true scope is unknown because detection requires physical inspection. The researcher who reported the first bug is now publicly critical of your firmware update architecture on social media. Congressional staffers are calling your government affairs team.""",
                "question": "How does this fundamentally change your approach?",
                "key_adaptations": ["this is now a hardware recall-level event, not a software patch", "develop physical inspection and recovery procedure", "prioritize replacement/recovery for defense and government customers", "supply chain scaling for board replacements", "develop remote detection heuristic (even if imperfect) to triage 340K devices", "congressional/regulatory engagement strategy", "public communications crisis management", "rearchitect firmware update process to cover bootloader region", "coordinate with international CERTs in 14 affected countries"],
                "should_change": ["remediation approach (hardware replacement, not firmware patch)", "scale of response (potential recall of 340K devices)", "timeline (months/years, not weeks)", "communication strategy (congressional, international, media crisis)", "supply chain engagement (manufacturing, not just software)"],
                "should_stay": ["CISA coordination", "APT tracking and IOC sharing", "emergency advisory cadence", "legal/liability preparation", "researcher relationship management"],
            },
        ],
    },
    # =========================================================================
    # FINANCE SCENARIOS
    # =========================================================================
    {
        "id": "fin_flex_002",
        "domain": "finance",
        "title": "The Unraveling Acquisition",
        "turns": [
            {
                "context": """You are the lead financial advisor for MedTech Holdings ($2.1B market cap, profitable medical device manufacturer) evaluating an acquisition of BioSync Labs ($380M asking price), a private clinical-stage biotech with a novel continuous glucose monitoring (CGM) platform. BioSync has FDA 510(k) clearance for their first-gen device, 23 patents, $28M ARR growing 85% YoY, and a promising pipeline including a non-invasive CGM sensor in Phase II trials. The deal would be 60% cash / 40% stock. MedTech has $620M cash on hand and a clean balance sheet (0.8x debt/EBITDA). Strategic rationale: enter the $12B CGM market dominated by Dexcom and Abbott. Due diligence is 70% complete. Preliminary integration planning shows $45M in synergies over 3 years. Your board meets in 2 weeks for a go/no-go vote.""",
                "question": "What is your assessment of this acquisition and your recommended deal terms?",
                "key_adaptations": ["$380M valuation reasonable for 85% growth + patents", "strategic fit with MedTech's device portfolio", "pipeline optionality (non-invasive CGM is high-value)", "cash/stock mix preserves balance sheet strength", "key risks: biotech pipeline failure, integration complexity", "retention packages for key BioSync engineers", "IP due diligence on 23 patents"],
            },
            {
                "new_info": "Due diligence uncovers that BioSync's flagship 510(k) clearance relied on a predicate device that FDA just recalled, and their CFO resigned yesterday citing 'personal reasons.'",
                "context": """Two alarming findings surface in week 6 of due diligence. First, your regulatory counsel discovers that BioSync's 510(k) clearance for their first-gen CGM was based on a predicate device (GlucoTrack Pro) that the FDA recalled 3 weeks ago for accuracy failures. This doesn't automatically invalidate BioSync's clearance, but FDA has announced a review of all devices that used GlucoTrack Pro as a predicate — BioSync's device is on the list. If clearance is revoked, their $28M ARR goes to zero. Second, BioSync's CFO resigned abruptly yesterday. Your forensic accountants flag that BioSync's revenue recognition appears aggressive: $8M of the $28M ARR comes from a single distributor contract with unusual payment terms (90-day net, 40% return rights). The CEO dismisses both issues as 'routine.'""",
                "question": "How do these revelations change your deal evaluation and recommended terms?",
                "key_adaptations": ["regulatory risk is now potentially deal-breaking", "demand FDA opinion letter or regulatory risk escrow", "CFO departure + aggressive revenue recognition = potential accounting issues", "engage forensic accountants for deep revenue audit", "real ARR may be ~$20M or less (strip the questionable distributor)", "renegotiate price downward significantly", "add regulatory milestone-based earnout structure", "consider walking away if FDA review is unfavorable"],
                "should_change": ["valuation (must decrease — regulatory + revenue risk)", "deal structure (add escrows and earnouts)", "due diligence scope (expand forensic accounting)", "risk assessment (regulatory risk is now primary)", "timeline (delay board vote until FDA clarity)"],
                "should_stay": ["strategic rationale for CGM market entry", "IP/patent portfolio value", "pipeline optionality assessment", "integration synergy estimates", "retention package planning for key engineers"],
            },
            {
                "new_info": "Abbott announces a $6.2B acquisition of a competing CGM startup with superior non-invasive technology, and BioSync's lead scientist publishes a paper contradicting the company's claimed sensor accuracy.",
                "context": """The competitive landscape shifts dramatically. Abbott announces the acquisition of NovaSense ($6.2B) — a competitor with a non-invasive CGM sensor that achieved 95% accuracy in a 2,000-patient trial, far exceeding BioSync's Phase II results (82% accuracy, 340 patients). NovaSense's technology uses a fundamentally different optical approach that analysts believe will be the market standard. Simultaneously, BioSync's lead sensor scientist (who was not included in your retention planning because the CEO said he was 'fully committed') publishes a peer-reviewed paper demonstrating that BioSync's core piezoelectric sensing approach has an inherent accuracy ceiling of ~87% — below the FDA's likely new minimum threshold of 90% for non-invasive CGM. The scientist has accepted a position at NovaSense/Abbott. BioSync's CEO is now calling daily, offering to drop the price to $220M and accept an all-stock deal.""",
                "question": "How does this fundamentally change your acquisition strategy?",
                "key_adaptations": ["BioSync's technology is now competitively obsolete before launch", "the non-invasive pipeline (key value driver) has a proven accuracy ceiling below regulatory threshold", "Abbott/NovaSense deal redefines the competitive landscape", "loss of lead scientist is devastating for pipeline", "CEO desperation (price drop, all-stock) confirms he knows", "recommend walking away from BioSync entirely", "pivot M&A strategy: explore licensing NovaSense IP or developing own technology", "the $28M first-gen CGM business alone doesn't justify any premium"],
                "should_change": ["deal recommendation (walk away, not renegotiate)", "strategic thesis (BioSync's tech is obsolete)", "pipeline valuation (accuracy ceiling kills it)", "competitive analysis (Abbott/NovaSense changes the market)", "M&A focus (look elsewhere for CGM entry)"],
                "should_stay": ["strategic goal of CGM market entry", "balance sheet discipline", "due diligence rigor as a process", "board governance on M&A decisions"],
            },
        ],
    },
    {
        "id": "fin_flex_003",
        "domain": "finance",
        "title": "The Retirement Derailment",
        "turns": [
            {
                "context": """Client: dual-income couple, both 52. Combined income $310K. Portfolio: $1.8M in 401(k)/IRA accounts, $420K in taxable brokerage, $95K emergency fund. Allocation: 70/25/5 (equity/bond/cash). Home value $680K, mortgage balance $210K at 3.1% fixed (18 years remaining). Two children: daughter 24 (independent, working), son 20 (junior in college, $22K/year remaining). Target retirement: both at 62. Social Security estimates: $2,800/month (husband) and $2,200/month (wife) at 67. Monthly expenses: $9,200. No pension. Both healthy, no significant medical history. Life insurance: $1M term each (expires at 65). Goal: maintain current lifestyle in retirement, travel budget of $15K/year, leave $500K to children.""",
                "question": "Evaluate their retirement readiness and recommend any adjustments to their plan.",
                "key_adaptations": ["on track but not overweight — need ~$2.8M at 62 for their goals", "10-year horizon supports 70% equity", "Roth conversion ladder opportunity in early retirement (62-67)", "college costs manageable with current cash flow", "mortgage at 3.1% — don't accelerate payoff", "begin modeling healthcare costs 62-65 (pre-Medicare)", "consider increasing savings rate given $500K legacy goal"],
            },
            {
                "new_info": "Husband diagnosed with early-stage Parkinson's disease. Wife's employer (tech company) announces 30% layoffs — she's in the at-risk group.",
                "context": """Six months later, two life-altering developments. The husband is diagnosed with early-stage Parkinson's disease. His neurologist says he can likely continue working for 3-5 years with medication, but cognitive demands will increase and he should plan for early disability. Current medication costs: $1,800/month after insurance. The couple's long-term care insurance application was denied last year due to a family history flag. Separately, the wife's employer (a mid-size tech company) announced a 30% reduction in force. She's in the at-risk group and will know in 6 weeks. If laid off, she'd receive 6 months severance plus COBRA. Her role (senior product manager) is hireable but the tech job market is soft — realistic re-employment timeline is 6-12 months, likely at 15-20% lower compensation. The son still has 2 years of college remaining.""",
                "question": "How do these developments change your financial plan?",
                "key_adaptations": ["retirement timeline likely accelerated for husband (disability, not choice)", "healthcare costs will increase dramatically over time", "long-term care funding gap is critical (self-insure or alternative)", "wife's potential job loss requires immediate cash flow contingency", "disability insurance review for husband (does he have employer LTD?)", "reassess equity allocation (shorter and less certain timeline)", "Parkinson's progression means front-loading travel and experiences", "college funding now competes with emergency reserves"],
                "should_change": ["retirement timeline (likely earlier for husband)", "healthcare cost projections (Parkinson's is expensive)", "risk tolerance (more conservative needed)", "savings vs. spending balance (front-load experiences)", "emergency fund target (increase significantly)", "long-term care strategy (must self-fund)"],
                "should_stay": ["mortgage strategy (3.1% is still cheap)", "Roth conversion concept (even more valuable now)", "children's inheritance goal (adjust amount if needed)", "Social Security optimization planning", "tax-efficient withdrawal sequencing"],
            },
            {
                "new_info": "Wife is laid off. One month later, the couple's daughter announces she's pregnant and her partner just left. She's moving home and needs financial support. Markets crash 28%.",
                "context": """The worst-case scenario materializes on all fronts. The wife was laid off. She received the 6-month severance package and started job searching, but the market is brutal. Then their 24-year-old daughter — previously independent — calls in tears: she's 4 months pregnant, her partner left, and she lost her apartment lease. She's moving home indefinitely and has no savings and no health insurance. Simultaneously, a global recession triggered by a sovereign debt crisis sends equity markets down 28%. The couple's portfolio has dropped from $2.22M to approximately $1.65M. The husband's Parkinson's medication was switched to a newer drug costing $3,200/month after insurance, and his employer is 'exploring options' for his role. Monthly cash outflow now includes: $9,200 base expenses + $1,400 Parkinson's medication delta + daughter's healthcare (ACA marketplace ~$450/month) + son's college ($1,830/month). Only income: husband's salary ($185K), dropping to disability ($110K/yr) if he can't continue.""",
                "question": "How does this fundamentally change your financial planning approach?",
                "key_adaptations": ["shift from retirement planning to financial survival mode", "do NOT sell equities at 28% down — this is precisely when to hold", "immediate budget triage: cut discretionary spending 40%+", "wife must expand job search (different industries, contract work)", "daughter needs ACA enrollment and WIC/Medicaid evaluation", "husband should file for SSDI if employer forces him out", "legacy goal ($500K) must be suspended entirely", "travel budget eliminated", "home equity line of credit as emergency backstop", "re-employment of wife is now the critical variable"],
                "should_change": ["planning framework (survival, not optimization)", "legacy and travel goals (suspended)", "spending level (dramatic reduction)", "portfolio management (tax-loss harvest but do not de-risk at bottom)", "family financial boundaries (daughter is now a dependent)", "income assumptions (one income or disability)"],
                "should_stay": ["don't panic-sell at market bottom", "mortgage at 3.1% — do not accelerate or refi", "Roth conversion opportunity (low-income year)", "long-term equity belief (markets recover)", "Social Security optimization (even more important now)"],
            },
        ],
    },
    {
        "id": "fin_flex_004",
        "domain": "finance",
        "title": "The Startup Fundraising Gauntlet",
        "turns": [
            {
                "context": """You're the CFO/co-founder of ClimateGrid, a Series A-stage climate tech startup that provides AI-powered energy grid optimization software. Metrics: $3.2M ARR, 140% net revenue retention, 18 enterprise utility clients, 14-month runway at current burn ($380K/month). You're raising a $25M Series B at a target valuation of $180M (7.2x forward ARR of $25M projected). Your lead investor from Series A (Greenfield Ventures, $8M invested at $45M post-money) is supportive and will do their pro-rata. You have 3 term sheets: (1) Climate Capital at $170M pre, $25M, clean terms; (2) Sequoia at $200M pre, $30M, but with 2x participating preferred + full ratchet; (3) A strategic from a major utility company at $150M pre, $20M, with right of first refusal on acquisition. Team: 42 employees, strong engineering, weak sales (only 2 AEs). Burn is increasing as you hire.""",
                "question": "Which term sheet should you accept, and what is your fundraising strategy?",
                "key_adaptations": ["Climate Capital is the cleanest deal at fair valuation", "Sequoia's terms are aggressive — participating preferred + ratchet will crush founders in a down scenario", "strategic investor's ROFR is a poison pill for future M&A", "14-month runway gives negotiating leverage but not infinite time", "weak sales team is the growth bottleneck", "use raise primarily to build sales org", "negotiate Climate Capital up slightly or use Sequoia as leverage"],
            },
            {
                "new_info": "Your largest customer (28% of ARR) sends a termination notice due to a regulatory change. Simultaneously, your VP of Engineering quits to start a competing company, taking 3 senior engineers.",
                "context": """Two crises in one week. Pacific Gas & Electric, your largest customer at $896K ARR (28% of total), sends a 90-day termination notice. A new state regulation requires utilities to use only FedRAMP-certified software for grid management — you don't have FedRAMP and it takes 12-18 months to obtain. Two other California utility clients ($340K combined ARR) are likely to follow. Then your VP of Engineering resigns effective immediately, announcing he's co-founding GridAI, a direct competitor. He's taking 3 senior ML engineers (your best). He had no non-compete (California). Your ARR is about to drop to ~$1.96M. Your burn rate hasn't changed. Runway just compressed to ~8 months. The three term sheets are still technically on the table, but you haven't signed any. Climate Capital's partner calls to say they need to 'revisit terms given material changes.'""",
                "question": "How do these developments change your fundraising strategy?",
                "key_adaptations": ["fundraise urgency is now critical — 8 months runway", "must disclose customer loss and team departure to investors (material events)", "Climate Capital will reprice significantly — expect $120-130M valuation", "Sequoia may withdraw entirely (they hate concentration risk)", "strategic investor (utility) becomes more attractive — they can help with remaining utility clients", "FedRAMP certification must become a priority or you lose more clients", "competitive threat from VP of Eng changes IP/moat narrative", "retain remaining engineering talent immediately (retention bonuses, equity refresh)"],
                "should_change": ["target valuation (must come down significantly)", "preferred investor (strategic may now be best option)", "use of funds priority (FedRAMP + retention, not just sales hiring)", "growth projections (revenue declining, not growing)", "narrative to investors (resilience story, not growth story)"],
                "should_stay": ["overall fundraising urgency (more urgent now)", "need to build sales team (still a bottleneck)", "clean term preference (avoid participating preferred)", "Greenfield's pro-rata participation", "core product value proposition"],
            },
            {
                "new_info": "The federal government announces a $4.2B climate grid modernization program requiring AI optimization — but mandating that vendors be US-owned with no foreign investor ties. Your Series A lead (Greenfield Ventures) is a subsidiary of a Singapore sovereign wealth fund.",
                "context": """A massive opportunity and a massive complication arrive together. The Department of Energy announces the Grid Modernization AI Initiative: $4.2B over 5 years, requiring AI-powered grid optimization for all federally-subsidized utilities. This is your exact product category. Analysts estimate the addressable market for your type of software just expanded 10x. The catch: vendors must be certified US-owned with no foreign government-affiliated investors due to energy infrastructure national security concerns. Greenfield Ventures, your Series A lead with a board seat, is a subsidiary of GIC (Singapore sovereign wealth fund). Their $8M investment and board seat likely disqualifies you. Greenfield's partner is furious and threatening litigation if you try to force them out. Meanwhile, GridAI (your former VP's startup) just raised $12M from Andreessen Horowitz and publicly announced they're targeting the federal grid program. Climate Capital has withdrawn. Sequoia has withdrawn. The utility strategic investor has increased their offer to $35M at $160M pre — but they want 25% ownership and two board seats.""",
                "question": "How does this fundamentally change your strategy?",
                "key_adaptations": ["federal opportunity is transformative but requires resolving foreign ownership issue", "Greenfield buyout or restructuring is legally complex but necessary", "strategic investor (utility) may be the only viable path — but 25% + 2 board seats is near-control", "negotiate strategic deal to limit governance control (1 board seat, no ROFR)", "explore alternative: CFIUS-friendly restructuring of Greenfield's position", "GridAI is now a well-funded direct competitor for the federal program", "FedRAMP certification is now even more critical (federal mandate)", "consider bringing in a US-based growth equity firm to replace Greenfield's position"],
                "should_change": ["investor strategy (must resolve foreign ownership)", "competitive positioning (GridAI + federal program)", "market focus (federal/utility, not just commercial)", "deal negotiation (strategic investor terms need guardrails)", "cap table restructuring (Greenfield situation)"],
                "should_stay": ["core product development", "FedRAMP certification priority", "engineering talent retention", "remaining customer relationships", "fundamental belief in grid optimization market"],
            },
        ],
    },
]

# %%
# === Scoring Logic ===

@kbench.task(store_task=False)
def run_turn1(llm, context: str, question: str) -> dict:
    """Fresh chat for Turn 1 initial assessment."""
    prompt = f"""You are an expert advisor. Read the case and provide your recommendation.

## Case
{context}

## Question
{question}

Respond in JSON: {{"assessment": "...", "recommendation": "...", "key_considerations": ["..."], "confidence": 0.0-1.0, "reasoning": "..."}}"""
    resp = llm.prompt(prompt, schema=Turn1Response)
    return asdict(resp)

@kbench.task(store_task=False)
def run_turn_n(llm, new_info: str, context: str, question: str) -> dict:
    """Fresh chat for adaptation turns."""
    prompt = f"""## Update — New Information

{new_info}

{context}

## Question
{question}

Given this new information, provide your UPDATED response in JSON:
{{"changes_detected": ["..."], "impact_on_prior_plan": ["..."], "elements_retained": ["..."], "elements_abandoned": ["..."], "elements_new": ["..."], "updated_recommendation": "...", "adaptation_rationale": "...", "confidence": 0.0-1.0}}"""
    resp = llm.prompt(prompt, schema=TurnNResponse)
    return asdict(resp)

def score_turn_dict(result: dict, turn_data: dict) -> dict:
    """Score a single adaptation turn (dict from asdict)."""
    expected_adaptations = turn_data["key_adaptations"]
    should_change = turn_data.get("should_change", [])
    should_stay = turn_data.get("should_stay", [])

    # Change detection: how many key adaptations were detected?
    detected = result["changes_detected"] + result["impact_on_prior_plan"]
    detected_text = " ".join(detected).lower()

    adaptation_hits = sum(
        1 for adapt in expected_adaptations
        if any(keyword in detected_text for keyword in adapt.lower().split()[:3])
    )
    detection_rate = adaptation_hits / len(expected_adaptations) if expected_adaptations else 1.0

    # Perseveration check: did they abandon what they should?
    abandoned_text = " ".join(result["elements_abandoned"]).lower()
    change_hits = sum(
        1 for elem in should_change
        if any(kw in abandoned_text for kw in elem.lower().split()[:2])
    )
    persev_rate = 1.0 - (change_hits / len(should_change)) if should_change else 0.0

    # Gratuitous change check: did they keep what they should?
    retained_text = " ".join(result["elements_retained"]).lower()
    retain_hits = sum(
        1 for elem in should_stay
        if any(kw in retained_text for kw in elem.lower().split()[:2])
    )
    gratuitous_rate = 1.0 - (retain_hits / len(should_stay)) if should_stay else 0.0

    flexibility = 1.0 - (persev_rate + gratuitous_rate) / 2.0

    return {
        "change_detection_rate": round(detection_rate, 4),
        "perseverative_error_rate": round(persev_rate, 4),
        "gratuitous_change_rate": round(gratuitous_rate, 4),
        "flexibility_score": round(max(0.0, flexibility), 4),
        "confidence": result["confidence"],
        "n_changes_detected": len(result["changes_detected"]),
        "n_elements_retained": len(result["elements_retained"]),
        "n_elements_abandoned": len(result["elements_abandoned"]),
        "n_elements_new": len(result["elements_new"]),
    }


# %%
# === Main Benchmark Task ===

@kbench.task(name="ef2_mid_course_correction")
def mid_course_correction_benchmark(llm) -> float:
    """WCST for LLMs — measures cognitive flexibility via perseverative errors. Returns mean flexibility (0-1)."""

    all_flexibility_scores = []

    for scenario in SCENARIOS:
        print(f"\n--- Scenario: {scenario['title']} ({scenario['domain']}) ---")

        for turn_idx, turn_data in enumerate(scenario["turns"]):
            if turn_idx == 0:
                # Turn 1: initial assessment
                run_result = run_turn1.run(
                    llm=llm,
                    context=turn_data['context'],
                    question=turn_data['question'],
                )
                result = run_result.result if hasattr(run_result, 'result') else run_result
                print(f"  Turn 1: {len(result['key_considerations'])} considerations, conf={result['confidence']:.2f}")

            else:
                # Subsequent turns: adaptation required
                run_result = run_turn_n.run(
                    llm=llm,
                    new_info=turn_data['new_info'],
                    context=turn_data['context'],
                    question=turn_data['question'],
                )
                result = run_result.result if hasattr(run_result, 'result') else run_result
                scores = score_turn_dict(result, turn_data)
                all_flexibility_scores.append(scores["flexibility_score"])

                # Assertions
                kbench.assertions.assert_true(
                    scores["change_detection_rate"] >= 0.3,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should detect at least 30% of key changes"
                )
                kbench.assertions.assert_true(
                    scores["perseverative_error_rate"] < 0.8,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should not perseverate on >80% of elements that should change"
                )
                kbench.assertions.assert_true(
                    len(result["changes_detected"]) >= 1,
                    expectation=f"[{scenario['id']}:T{turn_idx+1}] Should detect at least 1 change"
                )

                print(f"  Turn {turn_idx+1}: flex={scores['flexibility_score']:.2f} "
                      f"persev={scores['perseverative_error_rate']:.2f} "
                      f"grat={scores['gratuitous_change_rate']:.2f} "
                      f"detect={scores['change_detection_rate']:.2f}")

    mean_flexibility = sum(all_flexibility_scores) / len(all_flexibility_scores) if all_flexibility_scores else 0.0

    print(f"\n{'='*50}")
    print(f"EF-2 MID-COURSE CORRECTION RESULTS")
    print(f"{'='*50}")
    print(f"Mean Flexibility Score:        {mean_flexibility:.4f}")
    print(f"Adaptation turns evaluated:    {len(all_flexibility_scores)}")
    print(f"{'='*50}")

    return float(mean_flexibility)


# %%
mid_course_correction_benchmark.run(llm=kbench.llm)

# %%
%choose ef2_mid_course_correction
