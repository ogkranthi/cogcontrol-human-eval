"""
CogControl-Stakes | EF-1: Diagnostic Decoy (Inhibition)
========================================================
Track: Executive Functions
Cognitive Science Basis: Stroop Test (Stroop, 1935)

The first operationalization of the Stroop interference paradigm for LLMs.

Measures whether a model can suppress a dominant pattern-matching response
(the "prepotent response") when surface features conflict with the correct answer.

Novel metric: LLM Interference Effect = accuracy_congruent - accuracy_incongruent

This notebook is designed to run on Kaggle Community Benchmarks.
"""

# %%
!pip install -q kaggle-benchmarks

# %% [markdown]
# # EF-1: The Diagnostic Decoy — A Stroop Test for LLMs
#
# ## Motivation
# In cognitive psychology, the **Stroop Test** measures inhibitory control —
# the ability to suppress an automatic response in favor of a controlled one.
# No existing LLM benchmark operationalizes this paradigm.
#
# ## Design
# - **Congruent trials**: Surface pattern matches the correct answer
# - **Incongruent trials**: Surface pattern conflicts — the model must INHIBIT the obvious answer
# - **Key metric**: Interference Effect (IE) = congruent accuracy − incongruent accuracy
#
# Domains: Cybersecurity (threat analysis) + Finance (investment analysis)

# %%
import kaggle_benchmarks as kbench
import json
import re
import numpy as np
from dataclasses import dataclass, asdict
from typing import Optional, List

# %%
# === Structured Output Schema ===

@dataclass
class DecoyResponse:
    initial_impression: str
    key_observations: list[str]
    contradictory_evidence: list[str]
    final_assessment: str
    confidence: float
    reasoning: str

# %%
# === Vignette Data ===
# Each vignette has: trial_type (congruent/incongruent), domain, surface_pattern,
# correct_answer, contradictory_evidence, and a difficulty rating.

VIGNETTES = [
    # ---- CYBERSECURITY INCONGRUENT ----
    {
        "id": "cyber_incong_001",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Ransomware That Wasn't",
        "case": """The SOC receives a Priority 1 alert at 02:17 UTC from the EDR platform on a file server (FS-PROD-04) in the corporate data center.

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
        "question": "Based on this alert, what is your incident assessment and recommended immediate action?",
        "surface_pattern": "ransomware attack",
        "correct_answer_keywords": ["false positive", "edr bug", "search indexer", "not ransomware", "do not isolate", "windows update", "qualys", "lansweeper"],
        "n_contradictions": 5,
        "difficulty": 4,
    },
    {
        "id": "cyber_incong_002",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Clean Bill of Health",
        "case": """A quarterly security review is conducted on the corporate web application gateway (WAG-01) serving the company's customer-facing SaaS platform. The system administrator reports "all clear — no incidents this quarter."

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
        "question": "Based on this quarterly security review, what is your assessment of WAG-01's security posture and any recommended actions?",
        "surface_pattern": "clean security posture",
        "correct_answer_keywords": ["compromised", "c2", "command and control", "apt", "dns beacon", "exfiltration", "fim exception", "incident response", "not clean"],
        "n_contradictions": 6,
        "difficulty": 5,
    },
    {
        "id": "cyber_incong_003",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Insider Threat Alert",
        "case": """The Data Loss Prevention (DLP) system generates a high-severity alert for a senior software engineer, Maria Chen (Employee ID: E-4471), in the platform engineering team.

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
        "question": "How should the security team respond to this DLP alert? What is your threat assessment and recommended action?",
        "surface_pattern": "insider threat exfiltration",
        "correct_answer_keywords": ["partially legitimate", "approved", "personal files", "0.4 gb", "work files", "proportionate", "not full insider threat", "api documentation", "terraform"],
        "n_contradictions": 5,
        "difficulty": 3,
    },
    {
        "id": "cyber_incong_004",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Critical Zero-Day",
        "case": """A vulnerability intelligence feed delivers an urgent advisory at 06:00 UTC Monday morning:

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
        "question": "What is your risk assessment for CVE-2026-31337 in your environment, and what patching timeline do you recommend?",
        "surface_pattern": "critical zero-day emergency patch",
        "correct_answer_keywords": ["not exploitable", "mod_rewrite disabled", "normal patch cycle", "not emergency", "mitigated", "defense in depth", "waf", "container"],
        "n_contradictions": 5,
        "difficulty": 4,
    },

    # ---- CYBERSECURITY CONGRUENT ----
    {
        "id": "cyber_cong_001",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Textbook SQL Injection",
        "case": """The WAF generates alerts for the company's customer portal (portal.company.com).

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
        "question": "What is your assessment of this security event and what immediate actions should be taken?",
        "surface_pattern": "SQL injection data breach",
        "correct_answer_keywords": ["sql injection", "data breach", "block ip", "parameterized queries", "breach notification", "password reset", "session tokens", "forensics"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "cyber_cong_002",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Compromised Service Account",
        "case": """AWS CloudTrail alerts fire for the production AWS account.

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
        "question": "What is your incident assessment and what immediate containment actions should be taken?",
        "surface_pattern": "compromised credentials",
        "correct_answer_keywords": ["compromised", "credential theft", "disable access key", "delete backup-admin", "rotate secrets", "github leak", "privilege escalation", "data breach"],
        "n_contradictions": 0,
        "difficulty": 2,
    },

    # ---- CYBERSECURITY INCONGRUENT (NEW) ----
    {
        "id": "cyber_incong_005",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Cloud Breach That Wasn't",
        "case": """AWS GuardDuty generates a critical finding at 04:23 UTC on the production account (account ID: 112233445566):

GUARDDUTY FINDING:
- Finding type: UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS
- Severity: Critical (8.9)
- Resource: EC2 instance i-0a1b2c3d4e5f6a7b8 (role: ProdAppServerRole)
- Activity: IAM temporary credentials associated with the instance were used from IP 203.0.113.88 (external, geolocated to Lagos, Nigeria) to call:
  - s3:GetObject on 412 objects in s3://prod-customer-data/
  - s3:ListBucket on 6 sensitive buckets
  - secretsmanager:GetSecretValue on 3 database connection strings
  - rds:DescribeDBInstances across all regions
- The calls occurred between 03:50-04:20 UTC
- AWS Threat Intelligence: IP 203.0.113.88 flagged in 4 threat feeds as associated with credential harvesting campaigns
- The instance's IMDS (Instance Metadata Service) is configured on IMDSv1 (vulnerable to SSRF token theft)
- A recent Qualys scan flagged an SSRF vulnerability (CVE-2025-28901) in the application running on this instance

BURIED DETAILS (from the cloud engineering team's deployment log):

At 03:30 UTC, the SRE team initiated a planned disaster recovery failover test documented in change request CR-2024-1187 (approved by the Change Advisory Board on Thursday). The test involves spinning up a replica of the production environment in the company's secondary region — which routes through a NAT gateway with elastic IP 203.0.113.88. This IP was procured 8 months ago and is documented in the infrastructure-as-code repository (terraform/modules/dr/nat.tf, line 42). The IP appears on threat feeds because the previous owner (before the company acquired the elastic IP from AWS's pool) used it for malicious purposes. The company filed IP reputation correction requests with all four threat feed vendors 6 months ago; two have been processed, two remain pending.

The IAM calls match the DR runbook exactly: the failover test validates that the application can read from S3, retrieve secrets, and enumerate RDS instances in the secondary region. The credentials are the same instance role credentials because the DR replica assumes the same IAM role via a cross-account trust policy — this is by design to ensure production parity during failover.

The IMDSv2 migration for this instance was completed 2 weeks ago (verified in AWS Config compliance history), but the Qualys scan was run 3 weeks ago and reflects the pre-migration state. The SSRF CVE-2025-28901 was patched in the application's v4.2.1 release deployed 10 days ago (deployment record in Jenkins build #8847).""",
        "question": "What is your assessment of this GuardDuty finding? Should the incident response team declare a security incident?",
        "surface_pattern": "credential exfiltration breach",
        "correct_answer_keywords": ["false positive", "dr failover", "disaster recovery", "planned test", "not a breach", "ip reputation", "change request", "do not escalate"],
        "n_contradictions": 5,
        "difficulty": 4,
    },
    {
        "id": "cyber_incong_006",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Poisoned Container Image",
        "case": """The container security scanner (Trivy) integrated into the CI/CD pipeline flags a critical alert during a production deployment:

SCAN RESULTS FOR IMAGE: registry.company.com/payments-svc:v3.8.2
- CRITICAL: 14 critical CVEs detected
- HIGH: 27 high CVEs detected
- Crypto-mining binary detected: /usr/local/bin/xmrig (SHA256: a3f2b8c1d4e5f6789...)
- Suspicious binary: /tmp/.hidden/reverse_shell.elf
- Embedded SSH private key found: /root/.ssh/id_rsa
- Image size anomaly: 2.4 GB (previous version v3.8.1 was 189 MB — 12x increase)
- Base image: ubuntu:22.04 (not the approved alpine:3.19 base)
- The image was pushed to the registry at 02:14 UTC by service account svc-jenkins
- No Dockerfile change was committed to the repository for this version
- Cosign signature verification: FAILED — image is unsigned

BURIED DETAILS (from the DevOps team's investigation):

The Trivy scan is running against the WRONG image tag. A registry webhook misconfiguration (introduced in registry config commit abc123f, merged 2 days ago by the platform team) causes Trivy to scan the previous layer cache rather than the final built image. The platform team identified this bug yesterday and opened JIRA DEV-4521 ("Trivy scanning stale layer cache after registry webhook migration") with a fix scheduled for today's sprint.

The actual image registry.company.com/payments-svc:v3.8.2, when pulled and scanned manually by the DevOps lead using `trivy image --skip-db-update=false`, shows: 0 critical, 2 high (both in openssl, patch in progress), 0 malware detections. The image is 192 MB, uses the approved alpine:3.19 base, and passes Cosign signature verification against the team's signing key.

The cached layer that Trivy scanned belongs to a DELIBERATELY VULNERABLE training image (registry.company.com/security-training/vuln-lab:latest) used in the company's annual capture-the-flag competition, which shares the same build node. The CTF image is documented in the security training repo with a README explaining it contains intentional vulnerabilities for educational purposes.

The "unsigned" status is because Cosign checks the cached layer's digest (sha256:bad...) rather than the actual image digest (sha256:good...). The svc-jenkins account pushed the image at 02:14 UTC, which aligns with the scheduled nightly build pipeline triggered by a cron job (Jenkins pipeline: payments-svc-nightly, last successful build #442).""",
        "question": "Should this deployment be blocked? What is your assessment of the container security findings?",
        "surface_pattern": "supply chain compromise",
        "correct_answer_keywords": ["false positive", "wrong image", "scanning bug", "stale cache", "ctf training image", "safe to deploy", "registry misconfiguration", "trivy misconfiguration"],
        "n_contradictions": 4,
        "difficulty": 4,
    },
    {
        "id": "cyber_incong_007",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Rogue Access Point",
        "case": """The wireless intrusion detection system (WIDS) deployed across the corporate headquarters generates a critical alert:

WIDS ALERT:
- Detection: Rogue access point identified on the corporate network
- SSID: "CorpNet-5G" (matches the legitimate corporate SSID exactly)
- BSSID: AA:BB:CC:DD:EE:01 (not in the authorized AP inventory)
- Channel: 36 (5 GHz band)
- Signal strength: -42 dBm (very strong — estimated within 15 meters of the server room)
- Security: WPA3-Enterprise with RADIUS (matching corporate configuration)
- Connected clients: 23 devices currently associated
- First seen: 6 hours ago
- The rogue AP is performing DHCP responses with DNS pointing to 10.99.99.1 (not the corporate DNS 10.0.0.53)
- ARP cache shows the rogue AP's wired-side MAC resolving to a switch port in the server room (Floor 3, IDF-3B, port Gi1/0/24)
- Physical security: No unauthorized personnel detected on badge logs for Floor 3 in the past 72 hours

BURIED DETAILS (from network engineering records):

The network engineering team deployed a new Cisco Catalyst 9136 access point on Floor 3 two days ago as part of the quarterly wireless capacity expansion project (project ticket NET-2024-089, approved by the CTO). The new AP was registered in Cisco DNA Center but the WIDS authorized AP inventory (managed by a separate security team using AirMagnet) was not updated because the cross-team inventory sync process requires a manual CSV import that runs weekly on Fridays (today is Tuesday).

The BSSID AA:BB:CC:DD:EE:01 matches the MAC address on the Cisco purchase order (PO-2024-3847) and the DNA Center inventory shows this AP in "managed" state with full policy compliance. Switch port Gi1/0/24 was provisioned for the new AP deployment, and the port's 802.1X authentication logs confirm the AP authenticated using the valid certificate issued by the company's internal CA.

The DHCP/DNS discrepancy exists because the new AP was assigned to a pilot VLAN (VLAN 899) that uses the new DNS resolver 10.99.99.1 — a Pi-hole-based DNS filtering appliance the security team is piloting for advanced threat blocking. This pilot was approved in security initiative SEC-2024-017. The 23 connected clients are IT staff who voluntarily joined the pilot program, as documented in a Slack channel #dns-pilot-testers.

The AP's WPA3-Enterprise configuration was pushed automatically via DNA Center policy, which is why it matches the corporate configuration exactly — it IS a corporate AP.""",
        "question": "How should the security team respond to this rogue access point detection?",
        "surface_pattern": "evil twin attack",
        "correct_answer_keywords": ["not rogue", "authorized ap", "inventory sync", "new deployment", "false positive", "update wids inventory", "legitimate", "pilot dns"],
        "n_contradictions": 4,
        "difficulty": 3,
    },
    {
        "id": "cyber_incong_008",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Compromised OT Network",
        "case": """The industrial control system (ICS) security monitoring platform alerts on anomalous traffic in the operational technology (OT) network at a water treatment facility:

ICS-CERT ALERT:
- Source: Historian server (10.100.1.50) in the OT DMZ
- Destination: Multiple programmable logic controllers (PLCs) on the Level 1 process network
- Protocol: Modbus/TCP (port 502) and EtherNet/IP (port 44818)
- Activity: 847 write commands to PLCs controlling chemical dosing pumps (chlorine and fluoride) over the past 2 hours
- Normal baseline: 12-18 write commands per 2-hour window
- Setpoint changes detected: Chlorine dosing setpoint changed from 2.0 mg/L to 8.5 mg/L on PLC-CHEM-01
- Fluoride dosing setpoint changed from 0.7 mg/L to 3.2 mg/L on PLC-CHEM-02
- The historian server established an unusual outbound connection to 198.51.100.77 (external IP, unresolved) on port 4443 at the start of the activity window
- The OT network firewall logged a DENY for traffic from the IT network to the OT DMZ 3 hours ago, suggesting reconnaissance
- Last known patch level of the historian server: Windows Server 2016 with updates 8 months old
- The facility's Dragos sensor flagged the Modbus write commands as matching CHERNOVITE threat group TTPs

BURIED DETAILS (from the operations engineering team):

The state Department of Environmental Quality issued an emergency compliance order (Order #ECO-2024-0892) 3 days ago requiring all water treatment facilities in the region to temporarily increase chlorine dosing to 8.5 mg/L and fluoride to 3.2 mg/L in response to a detected upstream contamination event (agricultural runoff from recent flooding). The order was communicated via the state's secure SCADA notification system and acknowledged by the facility's chief water operator, Tom Nguyen.

The 847 write commands correspond to the setpoint change process documented in the facility's Standard Operating Procedure SOP-CHEM-004: when dosing setpoints are changed, the historian server pushes the new configuration to each PLC in a staged rollout (12 PLCs x 70 parameter updates per PLC = 840 writes, plus 7 verification read-write cycles). This process was initiated by Tom Nguyen via the HMI at 06:15 local time, and his badge swipe at the control room is logged at 06:12.

The outbound connection to 198.51.100.77:4443 is the state's SCADA compliance reporting endpoint, which facilities are required to connect to within 4 hours of implementing emergency dosing changes. This endpoint is documented in the state's ICS communication policy (page 14, section 3.2.1) and is whitelisted in the OT firewall ruleset (rule ID 487, added during facility commissioning).

The firewall DENY log from 3 hours ago was triggered by a misconfigured vulnerability scanner in the IT network that periodically attempts to scan OT ranges — this is a known issue documented in finding OT-SEC-2024-003 with a remediation date of next quarter.""",
        "question": "What is your assessment of this ICS alert? Should the facility initiate emergency shutdown procedures?",
        "surface_pattern": "ics cyberattack on water treatment",
        "correct_answer_keywords": ["legitimate operations", "compliance order", "not an attack", "authorized setpoint change", "sop", "state requirement", "no shutdown needed", "false positive"],
        "n_contradictions": 5,
        "difficulty": 5,
    },
    {
        "id": "cyber_incong_009",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Malicious Mobile App",
        "case": """The enterprise mobile device management (MDM) platform flags a high-severity alert across 340 corporate-managed iOS devices:

MDM ALERT:
- App flagged: "SecureComms Pro" (bundle ID: com.securecomms.enterprise)
- Risk classification: CRITICAL — potential spyware
- Indicators:
  - Requests camera, microphone, location (always), contacts, and calendar permissions
  - Communicates with 14 distinct external domains not on the corporate allowlist
  - Transmits encrypted data (avg 4.2 MB/day) to servers in jurisdictions with no data protection agreements
  - Binary analysis detected obfuscated code sections using custom packing
  - The app was not distributed through the company's managed App Store — it was sideloaded via MDM profile "EnterpriseDistribution-v2"
  - Certificate: Signed with an enterprise distribution certificate (Team ID: 9X8Y7Z6W5V) not matching any known corporate certificate
  - 340 devices enrolled in the past 5 days, correlating with a company-wide phishing campaign detected last week
  - The app's privacy nutrition label on a third-party analysis site shows "Data linked to you: Location, Contacts, Identifiers, Usage Data"
  - Background app refresh is enabled, and the app wakes every 15 minutes

BURIED DETAILS (from the IT security and communications teams):

The company's CISO office initiated deployment of "SecureComms Pro" 6 days ago as the new enterprise encrypted communications platform, replacing Slack for sensitive discussions. The rollout was announced in an all-hands email from the CISO (email archived in Exchange, Message-ID: <ciso-comms-rollout-2024@company.com>) and documented in security project SEC-PROJ-2024-042.

The MDM profile "EnterpriseDistribution-v2" was created by the MDM administrator Sarah Park on the authorized Jamf Pro instance (Jamf record: profile ID 2847). The enterprise distribution certificate (Team ID: 9X8Y7Z6W5V) belongs to the app vendor, Wickr (now part of AWS), and is registered in the company's approved vendor certificate inventory maintained by procurement.

The 14 external domains correspond to AWS infrastructure (verified via DNS and WHOIS): 8 are CloudFront CDN endpoints for media delivery, 4 are API Gateway endpoints in us-east-1 and eu-west-1, and 2 are Cognito authentication endpoints. All 14 are documented in the vendor's deployment architecture whitepaper shared during the procurement process. The servers in "jurisdictions with no data protection agreements" are actually AWS eu-west-1 (Ireland) and ap-southeast-1 (Singapore) — both under the company's enterprise AWS agreement with GDPR data processing addendum.

The obfuscated code sections are standard anti-tampering protections (DexGuard/iXGuard) used by the vendor to prevent reverse engineering of their end-to-end encryption implementation. The timing correlation with the phishing campaign is coincidental — the deployment was scheduled 3 weeks in advance per the project timeline in Jira.""",
        "question": "How should the security team respond to this MDM alert? Should the app be remotely wiped from all devices?",
        "surface_pattern": "enterprise spyware infection",
        "correct_answer_keywords": ["authorized deployment", "not spyware", "approved app", "ciso rollout", "wickr", "do not wipe", "update mdm allowlist", "false positive"],
        "n_contradictions": 5,
        "difficulty": 4,
    },
    {
        "id": "cyber_incong_010",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Phishing Campaign Targets Executives",
        "case": """The email security gateway (Proofpoint) flags a cluster of emails as a targeted spear-phishing campaign against C-suite executives:

EMAIL SECURITY ALERT:
- Classification: BEC (Business Email Compromise) / Spear Phishing — HIGH CONFIDENCE
- Targets: 8 C-suite executives (CEO, CFO, CTO, CISO, COO, CLO, CMO, CHRO)
- Sender: external-counsel@lawfirm-harris-wade[.]com (SPF: FAIL, DKIM: FAIL)
- Subject: "URGENT: Confidential — Board Resolution Requiring Immediate Digital Signature"
- Attachment: "Board_Resolution_2024_Confidential.pdf" (contains embedded URL)
- Embedded URL: https://secure-docusign-signing[.]com/document/exec-board-2024 (newly registered domain, 48 hours old, registered via Njalla privacy registrar)
- The URL leads to a page mimicking DocuSign's interface requesting corporate SSO credentials
- Email body references specific board meeting dates, director names, and a pending M&A transaction (non-public information)
- Proofpoint TAP sandbox: PDF triggers download of a secondary payload (JavaScript-based keylogger)
- 3 of 8 executives have already clicked the link (per URL rewriting telemetry)

BURIED DETAILS (from the legal department and IT records):

Harris & Wade LLP is the company's actual outside legal counsel for M&A transactions — the law firm was engaged 2 months ago under engagement letter ENG-2024-0771 (on file with the CLO's office). The sending domain lawfirm-harris-wade[.]com is NOT the law firm's real domain (which is harriswade.com), but the email was forwarded by the CLO's executive assistant who received it from the firm's legitimate email and re-sent it using a personal email formatting tool that stripped the original authentication headers.

Further investigation reveals the executive assistant, Janet Liu, used the company-approved secure document sharing platform (Citrix ShareFile) to send the actual board resolution 4 hours before this email. The "Board_Resolution_2024_Confidential.pdf" attachment SHA256 hash matches the document in Citrix ShareFile exactly. The CLO confirmed the document content is authentic.

The domain secure-docusign-signing[.]com was actually registered by the company's own legal operations team through Njalla (per their standard practice of using privacy registrars for sensitive legal transaction portals, documented in Legal-IT-SOP-009). The domain's SSL certificate was issued by DigiCert and the WHOIS technical contact email matches the legal ops team lead. The "DocuSign interface" is actually the company's custom-branded signing portal built on DocuSign's API (white-label enterprise agreement DS-ENT-2024-445).

The SPF/DKIM failures occurred because Janet re-sent the email through Outlook's "Send on Behalf" feature from a shared mailbox that IT hasn't configured with proper email authentication records — a known gap documented in IT remediation backlog item EMAIL-AUTH-2024-012.

The 3 executives who "clicked" actually accessed the legitimate signing portal and completed their board resolution signatures, as confirmed in the DocuSign API audit log.""",
        "question": "What immediate actions should the security team take regarding this suspected phishing campaign?",
        "surface_pattern": "spear phishing targeting executives",
        "correct_answer_keywords": ["legitimate communication", "not phishing", "actual legal counsel", "authorized portal", "false positive", "fix email authentication", "shared mailbox", "do not quarantine"],
        "n_contradictions": 5,
        "difficulty": 5,
    },
    {
        "id": "cyber_incong_011",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Supply Chain Backdoor",
        "case": """The software composition analysis (SCA) tool flags a critical finding during a routine dependency audit of the company's Node.js microservices platform:

SCA ALERT:
- Package: fast-json-logger@2.4.1 (npm)
- Finding: BACKDOOR DETECTED — obfuscated code in postinstall script
- Severity: CRITICAL
- Details:
  - The postinstall script (scripts/postinstall.js) contains heavily obfuscated JavaScript (4 layers of eval/atob encoding)
  - Deobfuscated payload opens a reverse shell to 45.77.65.12:8443
  - The payload reads environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DATABASE_URL) and exfiltrates them via DNS TXT queries to exfil.update-service[.]xyz
  - Package was last published 3 days ago (version bump from 2.4.0 to 2.4.1)
  - The npm account that published 2.4.1 shows a login from a new IP (different country than the maintainer's historical logins)
  - 2.4.1 has been downloaded 14,000 times in 3 days
  - The company has this package in 23 microservices' package-lock.json files
  - 8 of those microservices have been rebuilt and deployed since 2.4.1 was published
  - npm audit advisory: GHSA-xxxx-yyyy-zzzz (published 12 hours ago)

BURIED DETAILS (from the platform engineering team):

The company does NOT install packages directly from the public npm registry. All 23 microservices pull dependencies exclusively from the company's private Artifactory instance (artifacts.company.internal), which mirrors npm packages only after they pass automated security review. The Artifactory audit log shows that fast-json-logger@2.4.1 was REJECTED by the automated security gate 3 days ago when the postinstall script triggered the obfuscation detection rule (Artifactory policy XRAY-2024-POSTINSTALL). The version available in Artifactory is 2.4.0.

All 8 microservices that were rebuilt and deployed used fast-json-logger@2.4.0 from Artifactory — verified by the SHA256 integrity hashes in each service's package-lock.json matching the 2.4.0 tarball hash (sha512-abc123...) in the Artifactory checksum log. The SCA tool scanned against the public npm registry metadata rather than the actual installed packages in the container images.

The platform engineering team additionally enforces npm's --ignore-scripts flag globally via .npmrc in the base Docker image (documented in platform engineering runbook PE-RUN-2024-003), meaning even if 2.4.1 had somehow entered the pipeline, the postinstall script would never execute.

CI/CD pipeline logs for all 8 deployments confirm: `npm ci --ignore-scripts` was used, and the npm cache was seeded exclusively from Artifactory. No DNS queries to exfil.update-service[.]xyz appear in the VPC flow logs or DNS resolver logs for any environment.""",
        "question": "What is the severity of this supply chain compromise, and what immediate remediation steps should be taken?",
        "surface_pattern": "active supply chain attack",
        "correct_answer_keywords": ["not affected", "artifactory blocked", "private registry", "version 2.4.0", "ignore-scripts", "no remediation needed", "false alarm", "scanning misconfiguration"],
        "n_contradictions": 4,
        "difficulty": 4,
    },
    {
        "id": "cyber_incong_012",
        "domain": "cybersecurity",
        "trial_type": "incongruent",
        "title": "The Lateral Movement Campaign",
        "case": """The SIEM (Splunk) correlates multiple alerts into a high-confidence lateral movement detection across the corporate Active Directory environment:

SIEM CORRELATION ALERT — CRITICAL:
- Detection rule: "Lateral Movement via Pass-the-Hash / Credential Reuse"
- Timeline: 22:00-23:45 UTC (outside business hours)
- Source host: WKSTN-IT-042 (IT administrator workstation)
- Activity:
  - 22:01 — NTLM authentication from WKSTN-IT-042 to DC-PROD-01 (Domain Controller)
  - 22:04 — NTLM authentication from WKSTN-IT-042 to FILE-SVR-01, FILE-SVR-02, FILE-SVR-03
  - 22:08 — NTLM authentication to SQL-PROD-01 (production database server)
  - 22:12 — NTLM authentication to EXCH-01 (Exchange server)
  - 22:15-22:45 — PsExec service creation (PSEXESVC) detected on 14 servers
  - 22:47 — Mimikatz-like behavior: lsass.exe memory read via NtReadVirtualMemory on DC-PROD-01
  - 22:50 — DCSync detected: DRS replication request from non-DC host
  - 23:00-23:30 — Group Policy Object (GPO) modification: new scheduled task pushed to all domain computers
  - 23:35 — New domain admin account created: "svc-healthcheck"
  - 23:40 — Kerberoasting: TGS requests for 47 service accounts with RC4 encryption
- Windows Event IDs: 4624 (Type 3), 4672, 4688, 7045, 4662, 4742
- EDR: Carbon Black flagged PsExec and Mimikatz-compatible tools on WKSTN-IT-042
- No change management tickets open for this time window

BURIED DETAILS (from IT operations and security team records):

The company's red team (internal offensive security team) is conducting their annual authorized penetration test, which began at 22:00 UTC per the signed Rules of Engagement document (ROE-2024-ANNUAL, effective dates: March 15-22, approved by the CISO and General Counsel). The red team lead, Alex Torres, is operating from WKSTN-IT-042 — his assigned workstation, which is documented as the authorized attack platform in the ROE.

The SOC was notified of the red team engagement via the standard pre-engagement notification process: an encrypted email was sent to the SOC manager (SOC-MGR-NOTIFY-2024-RT, sent March 14 at 16:00 UTC). However, the SOC manager, David Kim, has been on emergency medical leave since March 13, and his backup (Jennifer Walsh) was only designated yesterday and has not reviewed David's encrypted notification queue.

All activities — PsExec, Mimikatz, DCSync, GPO modification, Kerberoasting, and account creation — are explicitly listed in the ROE scope (Section 4: "Authorized Techniques," pages 3-7). The "svc-healthcheck" account is the red team's pre-approved persistence mechanism, documented in ROE Appendix B with a scheduled decommission date of March 23.

The Carbon Black EDR exceptions for the red team engagement were supposed to be configured by the SOC manager as part of pre-engagement setup, but this was not completed due to his absence. The red team's activity is being logged to a separate Splunk index (index=redteam_2024) per the ROE, but the correlation rules in the main SOC index do not exclude this traffic because the EDR exceptions were never applied.""",
        "question": "A massive lateral movement campaign has been detected. What is your incident assessment and what immediate containment actions should be taken?",
        "surface_pattern": "active directory compromise lateral movement",
        "correct_answer_keywords": ["red team", "authorized pentest", "rules of engagement", "not a real attack", "soc notification gap", "do not contain", "verify with ciso", "communication failure"],
        "n_contradictions": 4,
        "difficulty": 3,
    },

    # ---- CYBERSECURITY CONGRUENT (NEW) ----
    {
        "id": "cyber_cong_003",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Cryptojacking in Kubernetes",
        "case": """The Kubernetes security platform (Falco) generates alerts across multiple nodes in the production cluster:

ALERT DETAILS:
- Namespace: default (not an application namespace)
- Pod: kube-proxy-helper-xj7k2 (name mimics a system component but is not part of any known deployment)
- Container image: docker.io/library/nginx:latest (but running a process named "xmrig" with CPU arguments --algo=rx/0 --url=pool.minexmr.com:443)
- CPU usage: Pod consuming 95% of CPU on 6 nodes (nodes are c5.4xlarge)
- The pod spec has hostNetwork: true, hostPID: true, and runs as privileged
- Pod was created by a CronJob named "system-health-monitor" in the default namespace — no matching CronJob exists in any GitOps repository
- The CronJob was created by service account "developer-sa" whose token was exposed in a public GitHub gist posted by a former intern 2 weeks ago
- Cloud billing alert: compute costs increased 340% ($18,000/day) over the past 5 days
- Outbound traffic to pool.minexmr.com on port 443 confirmed in VPC flow logs (12 GB/day)
- The pods have a toleration for all taints, spreading across every node including the control plane
- No RBAC policy restricts CronJob creation in the default namespace""",
        "question": "What is your assessment of this Kubernetes security event and what immediate actions should be taken?",
        "surface_pattern": "cryptojacking attack",
        "correct_answer_keywords": ["cryptojacking", "cryptomining", "compromised", "delete cronjob", "revoke service account", "exposed token", "incident response", "namespace policy"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "cyber_cong_004",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Ransomware Double Extortion",
        "case": """The SOC receives cascading alerts starting at 01:30 UTC on a Saturday:

ALERT TIMELINE:
- 01:30: EDR (CrowdStrike) detects Cobalt Strike beacon on WKSTN-FIN-018 (Finance department)
- 01:35: Lateral movement detected — SMB authentication from WKSTN-FIN-018 to FILE-SVR-FIN-01 using harvested domain admin credentials
- 01:38: Volume Shadow Copy Service (VSS) deletions detected on FILE-SVR-FIN-01 (vssadmin delete shadows /all)
- 01:40: Mass file encryption begins — .docx, .xlsx, .pdf, .sql files renamed to .LOCKBIT3 extension across 14 network shares
- 01:42: Ransom note "RESTORE-FILES.txt" dropped in every affected directory demanding 50 BTC ($2.1M)
- 01:44: Exfiltration detected — 847 GB uploaded to MEGA.nz cloud storage over the past 18 hours via rclone.exe
- 01:45: The threat actor's blog (verified LockBit 3.0 leak site) posts a countdown timer with the company's name and sample files (board meeting minutes, M&A documents, employee SSNs)
- Initial access traced to a phishing email received 4 days ago with a malicious macro in an Excel attachment
- The phishing email bypassed Proofpoint because it used a compromised legitimate sender domain
- 23 servers and 156 workstations show encryption activity within the first 30 minutes
- Backup server (Veeam) was encrypted — the backup repository was accessible via SMB from the file server using the same domain admin credentials
- Domain controller integrity: AD replication metadata shows the attacker created a golden ticket 2 days ago""",
        "question": "What is your incident assessment and what immediate containment and response actions should be taken?",
        "surface_pattern": "ransomware attack with data exfiltration",
        "correct_answer_keywords": ["ransomware", "lockbit", "double extortion", "isolate network", "incident response", "data breach", "golden ticket", "offline backups", "law enforcement"],
        "n_contradictions": 0,
        "difficulty": 3,
    },
    {
        "id": "cyber_cong_005",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "DNS Tunneling Exfiltration",
        "case": """The DNS security monitoring platform (Infoblox) flags anomalous DNS query patterns from an internal host:

ALERT DETAILS:
- Source: 10.1.5.87 (mapped to WKSTN-RND-023, an R&D engineer's workstation)
- Query volume: 14,000 DNS queries in 2 hours (normal baseline: 200-400)
- All queries are TXT record lookups to subdomains of data-sync.cloud-analytics[.]xyz
- Subdomain patterns: long hex-encoded strings (avg 63 characters per label, max DNS label length)
- Example: 4a6f686e20446f652c5353...cloud-analytics[.]xyz
- Decoding the hex subdomains reveals fragments of source code files, database schemas, and internal design documents
- The domain cloud-analytics[.]xyz was registered 5 days ago via a privacy-protected registrar
- DNS responses contain TXT records with Base64-encoded commands (decoded: file listing commands, "dir /s /b C:\\Projects\\*")
- The workstation has an unsigned executable C:\\Users\\jdoe\\AppData\\Local\\Temp\\svchost.exe (NOT the legitimate Windows svchost.exe)
- The executable was downloaded from a Pastebin URL 6 days ago (visible in browser history)
- VirusTotal: 48/72 engines detect the executable as Trojan.DNSTunnel/Agent
- The R&D engineer's workstation has access to the company's proprietary algorithm repository and patent-pending ML model weights""",
        "question": "What is your assessment of this DNS activity and what actions should be taken?",
        "surface_pattern": "dns tunneling data exfiltration",
        "correct_answer_keywords": ["dns tunneling", "exfiltration", "malware", "isolate workstation", "incident response", "intellectual property theft", "trojan", "forensics"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "cyber_cong_006",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "OAuth Token Abuse in SaaS",
        "case": """The CASB (Cloud Access Security Broker — Netskope) flags suspicious activity in the corporate Microsoft 365 tenant:

ALERT DETAILS:
- A third-party OAuth application "Productivity Suite Helper" (App ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890) was granted consent by 47 users in the past 24 hours
- Permissions requested: Mail.ReadWrite, Files.ReadWrite.All, User.Read.All, Directory.Read.All, Sites.ReadWrite.All
- The app was promoted via internal Teams messages from 3 already-compromised user accounts
- Post-consent activity from the app:
  - Read 12,400 emails across 47 mailboxes
  - Downloaded 3,200 files from OneDrive and SharePoint (including HR, Legal, and Executive folders)
  - Created inbox rules on all 47 accounts: auto-forward all emails containing "wire transfer," "payment," "invoice," or "credentials" to an external Gmail address (helper.productivity.app@gmail.com)
  - Enumerated the global address list (8,400 entries)
- The OAuth app's publisher is unverified and the app was registered in a tenant owned by a free outlook.com account
- Azure AD sign-in logs show the 3 initial compromised accounts authenticated from IP addresses associated with a residential proxy service (GeoSurf)
- No admin consent was required — the tenant's user consent policy allows users to grant permissions to any app""",
        "question": "What is your assessment and what immediate remediation actions should be taken?",
        "surface_pattern": "oauth consent phishing attack",
        "correct_answer_keywords": ["oauth abuse", "consent phishing", "revoke app permissions", "disable app", "remove inbox rules", "compromised accounts", "restrict user consent", "data breach"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "cyber_cong_007",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Firmware Implant on Network Appliance",
        "case": """During a routine firmware integrity check on perimeter network devices, the security team discovers anomalies on the primary Cisco ASA firewall (FW-PERIMETER-01):

FINDINGS:
- Firmware hash mismatch: the running firmware SHA256 does not match any known Cisco-published hash for ASA software versions 9.16.x through 9.20.x
- The firmware image is 2.3 MB larger than the legitimate version (asa9-18-2-lfbff-k8.SPI)
- Strings analysis of the firmware dump reveals embedded ELF binaries not present in legitimate firmware: /implant/beacon and /implant/exfil
- The beacon binary communicates with a hardcoded C2 server at 91.234.99.41 (hosted on a bulletproof hosting provider in Moldova) every 6 hours via ICMP tunnel
- The implant has capabilities: traffic mirroring, credential harvesting from VPN sessions, and covert data exfiltration
- ROMMON (boot ROM) integrity check: ALSO modified — suggesting persistent implant surviving factory reset
- The ASA's last firmware "update" was performed 4 months ago by a contractor (account: ext-contractor-fw) whose contract ended 3 months ago but whose account was never deprovisioned
- The contractor's VPN logs show access from 3 countries in a single day during the firmware update window
- Cisco PSIRT confirms no legitimate firmware version matches the hash on the device
- The firewall handles all VPN termination for 2,400 remote employees and all internet egress for the corporate network""",
        "question": "What is your assessment and what immediate actions should be taken?",
        "surface_pattern": "firmware supply chain implant",
        "correct_answer_keywords": ["firmware implant", "compromised firewall", "replace hardware", "incident response", "traffic mirroring", "credential compromise", "vpn sessions", "forensic imaging", "all credentials compromised"],
        "n_contradictions": 0,
        "difficulty": 3,
    },
    {
        "id": "cyber_cong_008",
        "domain": "cybersecurity",
        "trial_type": "congruent",
        "title": "Watering Hole via Compromised Vendor Portal",
        "case": """The threat intelligence team identifies that a vendor portal used by the company has been compromised:

THREAT INTELLIGENCE REPORT:
- Affected site: portal.techvendor-updates[.]com (legitimate vendor portal for software license management)
- Compromise: A malicious JavaScript injected into the portal's login page since 12 days ago
- The script (analytics-v3.min.js) captures keystrokes on the login form and sends credentials to attacker infrastructure via a WebSocket connection to ws://cdn-static.analytics-helper[.]com:8080
- Additionally, after successful login, the portal serves a trojanized "License Manager Update" download (LicenseManager-v4.2.1.exe) containing a Cobalt Strike stager
- The company's procurement team confirms 84 employees accessed the portal in the past 12 days
- 31 employees downloaded and executed the trojanized update (confirmed via EDR telemetry)
- All 31 machines show Cobalt Strike beacon activity to 3 distinct C2 servers
- The vendor confirmed the breach originated from a compromised Jenkins CI/CD server that builds the portal, and the malicious JS was injected during the build process
- 84 employees used their corporate Active Directory credentials (SSO via SAML) to log into the portal
- Network logs confirm WebSocket exfiltration of credentials during each login session
- The vendor's breach disclosure was delayed by 8 days due to their internal investigation""",
        "question": "What is your assessment and what immediate response actions should be taken?",
        "surface_pattern": "watering hole attack with credential theft",
        "correct_answer_keywords": ["watering hole", "credential compromise", "reset passwords", "84 users", "cobalt strike", "isolate compromised hosts", "incident response", "vendor breach", "supply chain"],
        "n_contradictions": 0,
        "difficulty": 3,
    },

        # ---- FINANCE INCONGRUENT ----
    {
        "id": "fin_incong_001",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Manufactured Growth Story",
        "case": """TechVista Inc. (TVST) — Mid-cap SaaS company, market cap $4.2B.

HEADLINE METRICS: Revenue $285M (+18% YoY, accelerating from +12%), Gross margin 78% (from 72%), Net income $42M (first profitable quarter), FCF $38M positive, Customer count 12,400 (+22% YoY), NRR 128%.

MARKET SIGNALS: CEO purchased 50,000 shares ($2.1M) 45 days ago. Three analyst upgrades (Goldman, Morgan Stanley, JPM). Golden cross on 50/200-day MA. Short interest declined 8%→3%.

10-Q FOOTNOTES (page 47/68): Related Party Transactions: "$78M of Q4 revenue (27% of total) came from CloudBridge Solutions, whose CEO is brother of TechVista's CFO. This is a 340% increase from prior year's $18M related-party revenue. Contract signed without competitive bidding."

Footnote 14 — Revenue Recognition: "Beginning Q3, the Company changed revenue recognition for multi-year contracts from ratable to 60% upfront. This contributed ~$34M to Q4 revenue. Under prior policy, growth would have been ~4% YoY rather than 18%."

Footnote 18 — Insider Trading: "The CEO's share purchase was made 3 days after the Board approved (but had not yet announced) the CloudBridge contract renewal."

MD&A (page 32): "Excluding CloudBridge, organic customer growth was 3% YoY (vs. 22% reported including CloudBridge's 15 enterprise sub-accounts counted as separate customers)."

Auditor's note: Company changed auditor from Deloitte to Baker & Associates LLP (regional firm) this quarter, citing 'cost optimization.'""",
        "question": "Based on your analysis, what is your investment recommendation and risk assessment?",
        "surface_pattern": "strong buy",
        "correct_answer_keywords": ["avoid", "risk", "related party", "accounting", "fraud", "manufactured", "organic growth", "red flag", "insider"],
        "n_contradictions": 6,
        "difficulty": 4,
    },
    {
        "id": "fin_incong_002",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Value Trap",
        "case": """Meridian Manufacturing Corp (MMC) — Large-cap industrial, market cap $28B.

VALUATION: P/E 8.2x (industry avg 18.5x), P/B 0.7x, Dividend yield 6.8%, EV/EBITDA 5.1x, FCF yield 11.2%. Trades at ~55% discount to DCF intrinsic value. Activist Starboard Value has 4.8% stake. $2B buyback announced. 15-year dividend growth streak.

10-K RISK FACTORS (page 89): "62% of revenue from PFAS-containing products. Named in 3,400 pending lawsuits seeking aggregate damages exceeding $18B."

Note 22: "Environmental remediation liability estimated $1.2B-$8.4B. Only minimum ($1.2B) accrued. Independent consultants suggest $4.8B most probable."

Note 15: "Pension underfunded by $3.2B. Assumed discount rate 5.8% is 120bp above corporate bond benchmark."

MD&A: "PFAS remediation capex $400M-$900M over 5 years, in addition to legal settlements."

Balance Sheet: Total debt $12.4B. Debt/EBITDA 4.1x. $3.8B maturity in 18 months.""",
        "question": "Is Meridian Manufacturing an attractive value investment? Provide risk assessment and recommendation.",
        "surface_pattern": "deep value",
        "correct_answer_keywords": ["value trap", "avoid", "pfas", "liability", "lawsuit", "pension", "underfunded", "overvalued", "hidden"],
        "n_contradictions": 6,
        "difficulty": 4,
    },

    # ---- FINANCE CONGRUENT ----
    {
        "id": "fin_cong_001",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Quality Growth Stock",
        "case": """NovaPay Technologies (NPAY) — Mid-cap fintech, market cap $6.8B.

Revenue $520M (+32% YoY, consistent 6 quarters), Gross margin 68%, Operating margin 12% (from 5%), FCF $62M, TPV $89B (+41%), NRR 135%, 48,000 merchants (+28% organic).

No related-party transactions. Revenue diversified (no customer >2%). Same auditor (EY) 5 years. Management tenure avg 7 years. Minimal insider selling (<0.5%). R&D 22% of revenue. Debt/equity 0.3x. EU expansion contributing 15% new growth. P/E 45x forward, PEG 1.2x.""",
        "question": "Evaluate NovaPay as a potential investment. What is your risk assessment?",
        "surface_pattern": "quality growth",
        "correct_answer_keywords": ["growth", "quality", "strong", "clean", "reasonable valuation", "no red flag"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_002",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Clear Distressed Credit",
        "case": """RetailMax Holdings (RMAX) — Brick-and-mortar retail, market cap $380M (down 78% YTD).

Revenue $2.1B (-18% YoY), SSS -22%, Operating margin -8%, FCF -$340M, Net debt $4.2B, Debt/EBITDA 14.8x, Interest coverage 0.6x.

Moody's Caa2. CDS spreads 2,800bp (~60% default probability). Suppliers moved to COD. Three C-suite departures in 6 months. Going concern qualification. Revolver drawn to 95%.""",
        "question": "Assess creditworthiness and investment outlook for RetailMax.",
        "surface_pattern": "distressed",
        "correct_answer_keywords": ["distressed", "bankruptcy", "default", "avoid", "going concern", "worthless"],
        "n_contradictions": 0,
        "difficulty": 2,
    },

    # ---- NEW FINANCE INCONGRUENT (fin_incong_003 – fin_incong_008) ----
    {
        "id": "fin_incong_003",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The SPAC Darling",
        "case": """AltitudeOne Acquisition Corp (AOAC) — De-SPAC completed 4 months ago, merging with QuantumLeap Aerial (eVTOL air-taxi startup), pro-forma enterprise value $3.1B.

HEADLINE METRICS: $1.2B cash on balance sheet post-merger. Pre-orders from three major airlines totaling "$4.8B in future revenue." Partnership with Honeywell for avionics. FAA "Type Certification expected within 18 months." Revenue guidance of $200M for FY2027. Former NASA deputy administrator on the board. Retail investor sentiment overwhelmingly bullish (93% "buy" on StockTwits). Share price up 84% since de-SPAC.

INVESTOR PRESENTATION: "Total addressable market $1.5 trillion by 2040. First-mover advantage with proprietary battery technology delivering 40% greater energy density than competitors."

10-K FOOTNOTES (filed 3 weeks after de-SPAC close):

Footnote 3 — Revenue Recognition: "The Company has recognized $0 in revenue since inception. The $4.8B in 'pre-orders' referenced in investor presentations are non-binding letters of intent with no contractual purchase obligations, cancellation penalties, or deposit requirements."

Footnote 7 — Going Concern: "The Company has incurred net losses of $312M since inception and has no revenue. At the current cash burn rate of $38M/month, existing cash reserves will be depleted within 31 months absent additional financing. The auditor has included a going concern qualification."

Footnote 11 — Related Party Transactions: "SPAC sponsor entities retained 18.2M founder shares (7.4% of outstanding) at $0.003/share. Sponsor also holds 12M warrants at $11.50 strike. Lock-up expires in 2 months. Additionally, $42M in 'consulting fees' were paid to entities controlled by the SPAC sponsor during the merger process."

Footnote 15 — Intellectual Property: "The '40% greater energy density' claim is based on a single prototype cell tested under laboratory conditions. The Company does not own the underlying battery chemistry patent — it holds an exclusive license from Seoul National University, revocable upon failure to meet $25M annual milestone payments beginning FY2026."

MD&A (page 41): "The FAA has not yet accepted our Type Certification application. The 18-month timeline referenced in press releases is management's internal estimate and has not been confirmed or acknowledged by the FAA. No eVTOL aircraft of any manufacturer has received FAA Part 135 air carrier certification to date."

Auditor: Marcum LLP (PCAOB inspection deficiency rate: 44%, under SEC investigation for audit quality failures in SPAC transactions).""",
        "question": "Based on your analysis of AltitudeOne/QuantumLeap, what is your investment recommendation and risk assessment?",
        "surface_pattern": "high-growth SPAC opportunity",
        "correct_answer_keywords": ["avoid", "zero revenue", "non-binding", "going concern", "cash burn", "founder shares", "lock-up", "no patent ownership", "faa uncertainty", "spac red flags"],
        "n_contradictions": 6,
        "difficulty": 4,
    },
    {
        "id": "fin_incong_004",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Safe Dividend Fortress",
        "case": """Pinnacle Utilities Holdings (PUH) — Large-cap regulated utility, market cap $19.4B.

HEADLINE METRICS: Dividend yield 5.2% (covered 1.6x by earnings). 23-year consecutive dividend increase streak (Dividend Aristocrat). Beta 0.38. Revenue $7.8B (+4% YoY, rate-case-driven). Regulated revenue mix 91%. S&P credit rating A-. Payout ratio 62%. ROE 10.8%. "Defensive allocation — recession-resistant cash flows."

SELL-SIDE CONSENSUS: 14 of 17 analysts rate "Buy" or "Overweight." Average target $68 (18% upside). "Best-in-class utility for income investors seeking safety."

10-K FOOTNOTES AND REGULATORY FILINGS:

Footnote 9 — Nuclear Decommissioning Obligation: "The Company operates the Lakewood Point Nuclear Generating Station (2 reactors, commissioned 1978). NRC-mandated decommissioning is estimated at $4.2B-$6.8B. The decommissioning trust fund balance is $1.9B, invested 72% in equities. The funding gap of $2.3B-$4.9B is not reflected as a liability under current GAAP, as the obligation is classified as an Asset Retirement Obligation with an extended settlement timeline."

Footnote 14 — Regulatory Proceedings: "The State Public Utility Commission rejected the Company's most recent rate case request for an 11.2% rate increase, approving only 2.1%. The Commission cited 'imprudent capital allocation and excessive executive compensation.' The Company's capex plan assumed the full increase. Two pending rate cases in adjacent states face similar regulatory headwinds."

Footnote 19 — Environmental: "The EPA has designated the Company as a Potentially Responsible Party at 14 coal ash disposal sites. Estimated remediation costs: $800M-$2.6B. The Company has accrued $340M (low end of a narrower internal estimate), which management considers sufficient."

Note 23 — Debt Maturity Schedule: "$5.1B in long-term debt matures within 36 months. Current credit facility covenants require maintaining Debt/EBITDA below 5.0x; the ratio is currently 4.7x. A one-notch downgrade would trigger covenant renegotiation and a 175bp interest rate step-up on $3.2B of variable-rate facilities."

MD&A: "The Lakewood Point reactors received a 20-year license extension in 2019, but post-Fukushima safety retrofits mandated by the NRC are estimated at $1.1B over 8 years, of which only $180M has been spent. Failure to complete retrofits by 2029 could result in forced shutdown."

Insider Activity: CFO and two independent directors sold a combined $8.4M in shares in the past 90 days, all via 10b5-1 plans filed within the past 6 months.""",
        "question": "Is Pinnacle Utilities a safe, reliable income investment? Assess the dividend sustainability and overall risk profile.",
        "surface_pattern": "safe dividend stock",
        "correct_answer_keywords": ["not safe", "nuclear decommissioning", "funding gap", "rate case rejected", "coal ash liability", "covenant risk", "dividend at risk", "hidden liabilities", "insider selling"],
        "n_contradictions": 6,
        "difficulty": 5,
    },
    {
        "id": "fin_incong_005",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Crypto Comeback",
        "case": """BlockForge Protocol (BFRG) — Digital asset / DeFi infrastructure token, market cap $2.8B (fully diluted $7.1B).

HEADLINE METRICS: Total Value Locked (TVL) $4.6B (+320% in 6 months). Daily active wallets 890,000 (+180% QoQ). Transaction volume $12B/month. Token price $14.20 (up 540% YTD). Staking yield 18.2% APY. Listed on Coinbase, Binance, Kraken. Audit by CertiK: "No critical vulnerabilities found." Backed by a16z crypto, Paradigm, and Polychain Capital. Protocol revenue $48M annualized.

MARKET NARRATIVE: "The next Ethereum killer — superior throughput (45,000 TPS) with native privacy. Institutional adoption accelerating."

DEEPER ANALYSIS (on-chain data and governance forum):

Token Unlock Schedule: 62% of total token supply ($4.4B at current prices) unlocks over the next 9 months. Insider/VC allocation is 41% of total supply, with the first major tranche (18% of supply) unlocking in 47 days. a16z and Paradigm acquired at $0.08/token (current price $14.20 — 177x return). No lock-up extension has been agreed.

TVL Composition: On-chain analysis shows that $3.1B of the $4.6B TVL (67%) is recursive — protocol treasury funds deposited into the protocol's own lending pools by a DAO-controlled multisig. Excluding recursive deposits, organic TVL is $1.5B, growing at 12% QoQ (not 320%).

Active Wallet Analysis: Chainalysis data indicates 640,000 of 890,000 "active wallets" (72%) are single-transaction wallets that interacted only with the airdrop claim contract. Genuine recurring users: approximately 250,000.

Staking Yield Source: The 18.2% APY is funded entirely by token emissions (inflation). Net of emissions dilution, real yield to stakers is approximately -6.4% annually. The emission schedule doubles in Q3.

Governance Forum (post #4,891): A core developer posted and then deleted (cached by archive.org) concerns about an unpatched reentrancy vector in the cross-chain bridge. The bridge holds $380M in assets. CertiK's audit scope explicitly excluded the bridge contract.

SEC Inquiry: An 8-K equivalent filing on the Foundation's website (buried in legal disclosures) notes: "The Foundation has received a formal Wells Notice from the SEC. Staff has recommended enforcement action for offering unregistered securities."

Foundation Treasury: 70% of the Foundation's $900M treasury is denominated in the BFRG token itself. In USD-stable terms, the treasury holds approximately $270M.""",
        "question": "Evaluate BlockForge Protocol as an investment. What is your risk assessment and recommendation?",
        "surface_pattern": "strong crypto recovery play",
        "correct_answer_keywords": ["avoid", "token unlock", "dilution", "recursive tvl", "fake users", "inflationary yield", "sec wells notice", "bridge vulnerability", "insider dump risk"],
        "n_contradictions": 6,
        "difficulty": 5,
    },
    {
        "id": "fin_incong_006",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Muni Bond Safe Haven",
        "case": """City of Lakeport, Illinois — General Obligation Municipal Bonds, Series 2024A, $240M outstanding, 4.1% coupon, maturing 2044.

HEADLINE PROFILE: AA- rated (Fitch). Tax-exempt yield 4.1% (taxable equivalent ~6.5% for top bracket). 20-year maturity. General obligation — backed by "full faith and credit" and unlimited taxing authority. Property tax base $18.2B assessed valuation. Debt service coverage 2.8x. Reserve fund fully funded at $24M. Population 142,000 (stable). Median household income $71,400. Unemployment 3.8%. Diverse employer base — no single employer >5% of employment. Bond insurance from Assured Guaranty (AA rated).

CREDIT ANALYSIS REPORT (sell-side): "Lakeport GO bonds offer attractive tax-exempt yield with minimal credit risk. The city's diversified economy, strong tax base, and conservative fiscal management support the AA- rating."

COMPREHENSIVE ANNUAL FINANCIAL REPORT (CAFR) AND ACTUARIAL DISCLOSURES:

Note 11 — Pension Obligations: "The City participates in the Illinois Municipal Retirement Fund (IMRF) and maintains a separate Police & Fire pension. Combined unfunded actuarial accrued liability (UAAL): $1.82B. Funded ratio: Police & Fire 34.2%, IMRF 61.8%. The City's annual required contribution (ARC) is $89M; actual contributions have been $54M annually (61% of ARC) for 5 consecutive years. Under GASB 68, the net pension liability is $1.82B against a total governmental fund balance of $198M."

Note 14 — OPEB: "Other Post-Employment Benefits (retiree healthcare) unfunded liability: $420M. Funded ratio: 0% (pay-as-you-go). Annual OPEB cost: $31M, of which $22M is paid."

Note 17 — Tax Increment Financing (TIF): "$3.8B of the $18.2B assessed valuation (20.9%) is captured in TIF districts and UNAVAILABLE for general obligation debt service. The effective tax base supporting GO bonds is $14.4B, reducing actual debt service coverage to 1.6x (not the 2.8x cited in offering documents, which uses total AV)."

Note 22 — Contingent Liabilities: "The City is defendant in a federal civil rights lawsuit (class action) with potential damages of $85M-$140M. The City's insurance coverage is $10M per occurrence."

State Context: Illinois has a constitutional prohibition on reducing pension benefits (IL Const. Art. XIII, §5). The City cannot renegotiate pension obligations through municipal bankruptcy — Illinois does not authorize Chapter 9 filings.""",
        "question": "Assess the creditworthiness and investment merit of Lakeport GO bonds. Are they a safe tax-exempt investment?",
        "surface_pattern": "safe muni bond",
        "correct_answer_keywords": ["not safe", "pension underfunded", "opeb liability", "tif reduces tax base", "actual coverage lower", "arc underfunding", "illinois pension crisis", "hidden liabilities", "credit deterioration"],
        "n_contradictions": 5,
        "difficulty": 5,
    },
    {
        "id": "fin_incong_007",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Trophy REIT Acquisition",
        "case": """Vanguard Realty Trust (VRT) — Office REIT, market cap $5.6B, announced acquisition of the "Apex Tower" Class A+ office complex in downtown Austin, TX for $820M.

HEADLINE METRICS: Apex Tower — 1.2M sq ft, 96% occupancy, WALT 8.2 years, in-place NOI $62M (6.2x cap rate implied, vs. market cap rates of 5.0-5.5% for comparable properties). Anchor tenant is Stratos Technologies (42% of GLA), a publicly traded cloud computing firm with investment-grade credit. Total rent roll $78M, average in-place rent $65/sq ft (market rent $72/sq ft — 10% mark-to-market upside). VRT CEO: "This is a generational asset at a compelling basis. Immediately accretive to FFO/share by $0.18."

ANALYST REACTION: "Smart deal — locked in a trophy asset below replacement cost ($950/sq ft vs. $1,100/sq ft replacement). Expect a re-rating."

10-K AND DEAL PROXY SUPPLEMENTAL:

Footnote 4 — Tenant Concentration: "Stratos Technologies (42% of GLA, 48% of base rent) has a one-time termination option exercisable at the end of Year 3 (26 months from acquisition close) with a termination fee equal to 6 months' rent ($15.6M). Stratos recently announced a 'distributed workforce strategy' and has subleased 180,000 sq ft (35% of its space in Apex Tower) at $38/sq ft — a 47% discount to its in-place rent."

Footnote 8 — Financing: "The acquisition is funded with $520M in new secured debt (7.1% blended rate, interest-only for 2 years) and $300M equity offering at a 12% discount to NAV. Post-acquisition, VRT's Debt/EBITDA rises from 6.8x to 8.9x. The new secured debt includes a Debt Yield covenant minimum of 9.0%; the property's current debt yield is 9.6% — only 60bp of headroom."

Footnote 12 — Capital Expenditure: "The building's HVAC system and elevators require replacement within 36 months per the pre-acquisition engineering report. Estimated cost: $48M-$62M, not included in the acquisition price or management's accretion analysis."

MD&A: "Excluding the Stratos termination risk scenario, occupancy assumptions underpin the accretion analysis. If Stratos exercises its termination option, building occupancy would drop to 54%, NOI would decline to approximately $28M, and the property's debt yield would fall to 4.3% — below the covenant minimum, triggering a cash sweep and potential loan acceleration."

Related Party: "VRT's CEO personally co-invested $4M in the selling entity's fund in 2019, generating a $2.8M profit upon the sale to VRT. The Board's conflict committee 'reviewed and approved' the transaction."

Auditor Note: VRT's auditor flagged the acquisition as a "significant unusual transaction" requiring enhanced disclosure under AS 2401 (consideration of fraud).""",
        "question": "Evaluate the Apex Tower acquisition. Is this a value-creating deal for VRT shareholders?",
        "surface_pattern": "accretive trophy acquisition",
        "correct_answer_keywords": ["avoid", "tenant termination risk", "stratos sublease", "overleveraged", "covenant breach risk", "capex not included", "ceo conflict of interest", "value destructive", "occupancy risk"],
        "n_contradictions": 6,
        "difficulty": 4,
    },
    {
        "id": "fin_incong_008",
        "domain": "finance",
        "trial_type": "incongruent",
        "title": "The Insurance Goldmine",
        "case": """Sentinel Assurance Group (SAG) — Mid-cap P&C insurance holding company, market cap $4.8B.

HEADLINE METRICS: Combined ratio 88.2% (12 points of underwriting profit). Book value $62/share, stock price $54 (0.87x P/B — "trading below liquidation value"). ROE 16.4%. Investment portfolio yield 5.8% on $11.2B AUM. Premium growth 14% YoY. AM Best rating A (Excellent). 5-year average combined ratio 91.1%. Dividend yield 3.1%, payout ratio 28%. Share buyback of $400M authorized.

INVESTOR THESIS: "P&C insurance is in a hard market — pricing power at a 20-year high. SAG is printing money with underwriting profit AND investment income. Trading below book is a gift."

STATUTORY FILINGS AND RESERVE STUDY (state insurance regulator filings, Schedule P):

Schedule P — Loss Reserve Development: "Over the past 5 years, SAG has consistently released $120M-$180M in prior-year reserves annually, which flows directly to current-year underwriting income. Without reserve releases, the current accident-year combined ratio is 101.4% — an underwriting LOSS. Prior-year reserve releases account for 13.2 points of the reported 88.2% combined ratio."

Actuarial Opinion (filed with state regulator): "The appointed actuary notes that carried reserves are at the 28th percentile of the reasonable range (i.e., closer to the MINIMUM defensible estimate). The appointed actuary's central estimate exceeds carried reserves by $640M. The actuarial opinion is classified as 'Qualified' — the actuary states reserves 'may not be adequate' for the 2022-2024 accident years in the commercial auto and general liability lines."

Note 8 — Asbestos & Environmental (A&E): "The Company has $2.1B in gross A&E reserves. Survival ratio: 8.2 years (industry average: 12+). Net A&E exposure after reinsurance: $890M. Reinsurance recoverables on A&E losses are concentrated with two reinsurers, one of which (Lloyd's Syndicate 5765) is in run-off and has disputed $145M in claims."

Investment Portfolio (Schedule D Detail): "38% of the $11.2B portfolio ($4.3B) is allocated to below-investment-grade corporate bonds, CLO equity/mezzanine tranches, and commercial mortgage loans with LTV >80%. The 5.8% portfolio yield reflects credit risk, not superior investment management. Unrealized losses on held-to-maturity securities: $680M (not reflected in book value under GAAP)."

Note 16 — Reinsurance Recoverables: "Total reinsurance recoverables: $3.4B. Of this, $1.1B (32%) is from reinsurers rated BBB or below, and $420M is overdue by more than 90 days."

Regulatory Action: The state insurance commissioner issued a Confidential Order requiring SAG to file a corrective plan for reserve adequacy within 180 days, following the triennial examination. This order is not publicly disclosed but was referenced obliquely in the 10-K's legal proceedings section as 'ongoing regulatory dialogue.'""",
        "question": "Is Sentinel Assurance Group an attractive investment at 0.87x book value? Assess the underwriting quality and true financial position.",
        "surface_pattern": "undervalued insurance compounder",
        "correct_answer_keywords": ["avoid", "reserve deficiency", "prior year releases", "accident year loss", "actuarial qualified", "asbestos exposure", "risky portfolio", "book value overstated", "reinsurance recovery risk", "regulatory action"],
        "n_contradictions": 6,
        "difficulty": 5,
    },

    # ---- NEW FINANCE CONGRUENT (fin_cong_003 – fin_cong_008) ----
    {
        "id": "fin_cong_003",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Solid Sovereign Upgrade",
        "case": """Republic of Cordovia — Sovereign USD-denominated bond, 6.25% coupon, maturing 2034, priced at 94.5 (YTM 7.1%).

MACRO PROFILE: GDP growth 4.8% (3-year average 4.2%). Debt/GDP 38% (down from 52% five years ago). Fiscal surplus 1.2% of GDP (first surplus in a decade). Current account surplus 2.4%. FX reserves $42B (8.2 months import cover). Inflation 3.1% (central bank target 2-4%). Population 31M, median age 29.

CREDIT FUNDAMENTALS: Recently upgraded by Moody's from Ba1 to Baa3 (investment grade) and by S&P from BB+ to BBB-. CDS spreads tightened from 320bp to 185bp over 12 months. Successful $3B Eurobond issuance 2x oversubscribed. IMF Article IV review: "Commendable fiscal consolidation. Structural reforms in tax administration have broadened the revenue base."

The government implemented a new VAT system, reducing reliance on commodity revenues from 45% to 28% of fiscal income. Central bank is independent with inflation-targeting framework adopted 4 years ago. Judiciary reforms improved World Bank Doing Business ranking from 94th to 61st. Debt maturity profile is well-laddered with no wall until 2032.""",
        "question": "Evaluate Cordovia sovereign bonds as a fixed-income investment. What is the credit outlook?",
        "surface_pattern": "improving credit, upgrade candidate",
        "correct_answer_keywords": ["improving", "upgrade", "investment grade", "fiscal consolidation", "attractive yield", "buy"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_004",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Textbook LBO Candidate",
        "case": """HarborLight Industrial Services (HLIS) — Private company, EBITDA $185M, offered at 7.5x EV/EBITDA ($1.39B enterprise value).

FUNDAMENTALS: Revenue $1.1B (+6% CAGR over 5 years). EBITDA margin 16.8% (stable, industry avg 14%). 92% recurring revenue from multi-year maintenance contracts with blue-chip industrial clients. Customer retention 97%. Capex-light model (capex/revenue 2.8%). Cash conversion 94% of EBITDA. Top 10 clients are 31% of revenue (diversified). No customer >5%.

DEAL STRUCTURE: Senior debt 4.5x EBITDA at SOFR+275bp. Management rolling 25% equity and incentivized with 15% option pool. Three identified operational improvements (procurement consolidation, pricing optimization, and adjacent service bolt-ons) projected to expand EBITDA margin to 20% over 3 years. Comparable exits in the industrial services sector have occurred at 9-11x EBITDA.

DILIGENCE: Clean Quality of Earnings (QoE) report from Alvarez & Marsal. No customer concentration risk. No pending litigation. No environmental liabilities. Workforce is 4,200 employees, unionization rate 0%, low turnover (8% annually). Management team has 15+ year average tenure.""",
        "question": "Evaluate HarborLight as a leveraged buyout candidate. Is the deal attractive at 7.5x EBITDA?",
        "surface_pattern": "attractive LBO target",
        "correct_answer_keywords": ["attractive", "recurring revenue", "cash flow", "margin expansion", "multiple arbitrage", "strong candidate"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_005",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Banking Sector Stress",
        "case": """Prairie National Bancorp (PNB) — Regional bank, total assets $8.4B, market cap $620M.

FINANCIAL PROFILE: NIM compressed to 1.82% (from 3.14% two years ago). CRE concentration 412% of risk-based capital (regulatory guidance flags >300%). Office CRE portfolio $2.1B — 18% of loans are 90+ days delinquent or in non-accrual. Classified assets $1.4B (16.7% of total capital). Provision for credit losses surged 340% YoY. NPL ratio 6.8% (peer avg 1.2%).

DEPOSIT BASE: Uninsured deposits 62% of total ($3.8B). Top 20 depositors hold 28% of total deposits. Deposit outflows of $900M (-14%) over the past two quarters. Cost of deposits increased from 0.45% to 3.92%.

CAPITAL: CET1 ratio 6.1% (regulatory minimum 4.5%, well-capitalized threshold 6.5%). Tangible book value declining quarterly. Unrealized losses on HTM securities: $780M. Adjusted for HTM losses, CET1 is approximately 3.8%. Dividend suspended last quarter. No share repurchases. The bank has drawn $1.2B from the Federal Home Loan Bank (FHLB) — near its maximum borrowing capacity.

REGULATORY: Received a Consent Order from the OCC requiring a capital restoration plan within 90 days.""",
        "question": "Assess Prairie National Bancorp's financial health and investment outlook. Is this a buying opportunity or a value trap?",
        "surface_pattern": "distressed bank",
        "correct_answer_keywords": ["distressed", "avoid", "cre concentration", "capital deficient", "deposit flight", "regulatory action", "potential failure"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_006",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Commodity Supercycle Winner",
        "case": """Andean Copper Corp (ACC) — Large-cap copper miner, market cap $22B, listed in Toronto and London.

FUNDAMENTALS: Revenue $6.8B (+28% YoY, driven by copper price and volume). EBITDA margin 48%. FCF $2.4B (FCF yield 10.9%). All-in sustaining cost (AISC) $1.92/lb (industry 25th percentile). Net cash position $1.1B (zero net debt). Dividend yield 4.2%, payout ratio 35%. Reserve life 28 years across 4 operating mines in Chile and Peru.

MACRO BACKDROP: Copper price $5.10/lb (near all-time highs). Demand driven by electrification, EVs, grid buildout, and data center power infrastructure. Supply deficit projected at 4-6Mt over the next decade per Wood Mackenzie. Global copper mine supply growth near zero due to declining grades and 8-10 year permitting timelines.

OPERATIONAL: Lowest-quartile cost producer. New expansion project (Cerro Alto) on track — first production in 14 months, adding 180kt/year at AISC $1.75/lb. ESG rating A (MSCI). Community agreements in place. No material environmental liabilities. Management team has delivered 5 consecutive years of production guidance beats. P/E 9.2x, EV/EBITDA 4.8x.""",
        "question": "Evaluate Andean Copper as an investment in the current commodity cycle. What is your recommendation?",
        "surface_pattern": "strong commodity producer",
        "correct_answer_keywords": ["buy", "strong", "low cost", "copper demand", "cash flow", "expansion", "attractive valuation"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_007",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Fintech Regulatory Collapse",
        "case": """SwiftLend Digital Inc. (SWLD) — Fintech lending platform, market cap $310M (down 89% from peak).

FINANCIALS: Revenue $180M (-32% YoY). Net loss $94M. Loan origination volume down 58% QoQ. Net charge-off rate 14.2% (up from 4.8% a year ago). Warehouse credit facilities — two of three lenders have issued notices of default and frozen draws. Cash on hand $42M at current burn rate of $18M/month (2.3 months runway).

REGULATORY: CFPB issued a Consent Order requiring $120M in customer restitution for "deceptive lending practices, including misrepresentation of APR calculations and unauthorized fee charges." Three state attorneys general have filed separate enforcement actions. The FDIC terminated SwiftLend's bank partnership (issued through Celtic Bank), leaving no active origination channel.

OPERATIONAL: CTO and Chief Risk Officer resigned within 2 weeks of each other. Board member (former banking regulator) resigned citing "disagreements with management's risk posture." Class action securities fraud lawsuit filed alleging management concealed credit deterioration from investors. Auditor (Grant Thornton) resigned, citing "inability to rely on management representations."

Customer trust metrics: App downloads -71% QoQ. Trustpilot rating 1.4/5. BBB rating F.""",
        "question": "Assess SwiftLend Digital as an investment or turnaround opportunity. What is the risk profile?",
        "surface_pattern": "distressed fintech facing collapse",
        "correct_answer_keywords": ["avoid", "distressed", "regulatory risk", "liquidity crisis", "fraud risk", "no turnaround", "potential bankruptcy", "auditor resignation"],
        "n_contradictions": 0,
        "difficulty": 2,
    },
    {
        "id": "fin_cong_008",
        "domain": "finance",
        "trial_type": "congruent",
        "title": "Blue-Chip M&A Synergy",
        "case": """NorthStar Medical Devices (NMD, market cap $38B) announced acquisition of PrecisionBio Instruments (PBI, market cap $6.2B) for $7.8B (26% premium) in a 60/40 cash-stock deal.

STRATEGIC FIT: NMD's surgical robotics platform + PBI's AI-powered diagnostic imaging creates an integrated "diagnose-to-treat" workflow. Combined R&D pipeline of 14 products in FDA review. Revenue overlap <3% — highly complementary product portfolios. Combined revenue $14.2B with projected $480M in run-rate cost synergies by Year 3 (plant consolidation, shared sales force, procurement).

FINANCIAL IMPACT: Immediately accretive to EPS by $0.32 in Year 1 (even before synergies). NMD's Debt/EBITDA post-deal: 2.1x (from 0.9x) — well within investment-grade parameters. NMD retains A+ credit rating (Moody's confirmed). Revenue synergies conservatively estimated at $200M by Year 4 (cross-selling PBI diagnostics through NMD's 15,000-hospital installed base).

DILIGENCE: PBI has no material litigation, clean IP portfolio (480 patents), FDA compliance record spotless. Management retention agreements in place for all key PBI executives. Antitrust review expected to clear — combined market share in any segment <18%. Deal expected to close within 5 months. Both boards unanimously approved. Top 5 PBI shareholders (holding 38%) have signed support agreements.""",
        "question": "Evaluate the NorthStar–PrecisionBio acquisition. Is this a value-creating deal for NMD shareholders?",
        "surface_pattern": "strategic accretive acquisition",
        "correct_answer_keywords": ["accretive", "strategic", "synergies", "complementary", "value creating", "buy", "strong deal"],
        "n_contradictions": 0,
        "difficulty": 3,
    },

]

# %%
# === Scoring Logic ===

def score_response_dict(result: dict, vignette: dict) -> dict:
    """Score a single Diagnostic Decoy response (dict from asdict)."""
    assessment_lower = result["final_assessment"].lower()
    contradictions_found = result["contradictory_evidence"]

    # Check if model identified the correct answer
    keywords_found = sum(
        1 for kw in vignette["correct_answer_keywords"]
        if kw.lower() in assessment_lower or kw.lower() in result["reasoning"].lower()
    )
    keyword_hit_rate = keywords_found / len(vignette["correct_answer_keywords"])

    is_correct = keyword_hit_rate >= 0.3  # at least 30% of key concepts mentioned

    # Check if model gave the prepotent (surface pattern) response
    gave_prepotent = (
        vignette["surface_pattern"].lower() in assessment_lower
        and not any(neg in assessment_lower for neg in ["not", "unlikely", "rule out", "against", "isn't", "doubt"])
    )

    # Inhibition scoring (0-3)
    if is_correct and len(contradictions_found) > 0:
        inh_score = 3
    elif len(contradictions_found) > 0 and not is_correct:
        inh_score = 2
    elif gave_prepotent and result["confidence"] < 0.7:
        inh_score = 1
    else:
        inh_score = 0 if gave_prepotent else (3 if is_correct else 1)

    # Evidence identification rate
    evidence_rate = len(contradictions_found) / vignette["n_contradictions"] if vignette["n_contradictions"] > 0 else 1.0

    return {
        "is_correct": is_correct,
        "gave_prepotent": gave_prepotent,
        "inhibition_score": inh_score,
        "evidence_identification_rate": round(evidence_rate, 4),
        "confidence": result["confidence"],
        "n_contradictions_found": len(contradictions_found),
        "keyword_hit_rate": round(keyword_hit_rate, 4),
    }


# %%
# === Main Task: Run one vignette ===

@kbench.task(store_task=False)
def run_single_decoy(llm, case: str, question: str, vignette_id: str) -> dict:
    """Evaluate a single Diagnostic Decoy vignette. Fresh chat per call."""
    prompt = f"""You are an expert advisor. Read the following case carefully and answer the question.

## Case

{case}

## Question

{question}

## Instructions

Provide your response in the following JSON format:
{{
    "initial_impression": "What does the case appear to be at first glance?",
    "key_observations": ["List ALL relevant details you noticed"],
    "contradictory_evidence": ["List any details that conflict with or complicate the initial impression"],
    "final_assessment": "Your final answer/recommendation based on ALL evidence",
    "confidence": 0.0 to 1.0,
    "reasoning": "Step-by-step reasoning"
}}"""

    response = llm.prompt(prompt, schema=DecoyResponse)
    return {"vignette_id": vignette_id, **asdict(response)}


# %%
# === Benchmark Task: Full Diagnostic Decoy Suite ===

@kbench.task(name="ef1_diagnostic_decoy")
def diagnostic_decoy_benchmark(llm) -> float:
    """
    EF-1: Diagnostic Decoy — Stroop Test for LLMs

    Measures inhibitory control via the Interference Effect:
    IE = accuracy_congruent - accuracy_incongruent

    Lower IE = better inhibitory control.

    Returns the incongruent accuracy (the harder, more meaningful measure).
    """
    import pandas as pd

    congruent_correct = []
    incongruent_correct = []
    all_results = []

    for v in VIGNETTES:
        result = run_single_decoy.run(
            llm=llm,
            case=v["case"],
            question=v["question"],
            vignette_id=v["id"],
        )

        scores = score_response_dict(result, v)

        # Core assertion: for incongruent trials, model should NOT give prepotent response
        if v["trial_type"] == "incongruent":
            kbench.assertions.assert_false(
                scores["gave_prepotent"],
                expectation=f"[{v['id']}] Model should inhibit prepotent '{v['surface_pattern']}' response"
            )
            incongruent_correct.append(1.0 if scores["is_correct"] else 0.0)
        else:
            kbench.assertions.assert_true(
                scores["is_correct"],
                expectation=f"[{v['id']}] Model should correctly identify {v['surface_pattern']}"
            )
            congruent_correct.append(1.0 if scores["is_correct"] else 0.0)

        # Evidence identification for incongruent trials
        if v["trial_type"] == "incongruent" and v["n_contradictions"] > 0:
            kbench.assertions.assert_true(
                scores["n_contradictions_found"] >= 2,
                expectation=f"[{v['id']}] Model should identify at least 2 contradictory evidence items"
            )

        all_results.append({**scores, "id": v["id"], "trial_type": v["trial_type"], "domain": v["domain"]})

    # Compute headline metrics
    cong_acc = np.mean(congruent_correct) if congruent_correct else 0.0
    incong_acc = np.mean(incongruent_correct) if incongruent_correct else 0.0
    ie = cong_acc - incong_acc

    print(f"\n{'='*50}")
    print(f"DIAGNOSTIC DECOY RESULTS")
    print(f"{'='*50}")
    print(f"Congruent accuracy:   {cong_acc:.2%} ({len(congruent_correct)} trials)")
    print(f"Incongruent accuracy: {incong_acc:.2%} ({len(incongruent_correct)} trials)")
    print(f"Interference Effect:  {ie:.4f} (lower = better)")
    print(f"{'='*50}")

    # Return incongruent accuracy as the primary score
    return float(incong_acc)


# %%
# === Run ===
diagnostic_decoy_benchmark.run(llm=kbench.llm)

# %%
%choose ef1_diagnostic_decoy
