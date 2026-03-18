"""
CogControl-Stakes | MC-1: Calibrated Confidence Under Stakes
=============================================================
Track: Metacognition
Cognitive Science Basis: Nelson & Narens (1990) Monitoring-Control Framework
                        Persaud et al. (2007) Wagering Paradigm

Tests whether models can accurately assess their own confidence using
a behavioral wagering paradigm — not just verbalized confidence.

Novel metric: Wager-Weighted Accuracy (exponential penalty for overconfidence)
"""

# %%
!pip install -q kaggle-benchmarks

# %% [markdown]
# # MC-1: Calibrated Confidence Under Stakes
#
# ## Motivation
# Existing calibration benchmarks ask models to state confidence verbally.
# But verbalized confidence is poorly calibrated in LLMs (NAACL 2024).
# This benchmark uses a **wagering paradigm** — the model must bet points
# on its answers, creating a behavioral metacognitive test.
#
# ## Domains
# - **Cybersecurity**: Vulnerability severity / attack identification (5 difficulty tiers)
# - **Finance**: Risk factor materiality assessment (SEC EDGAR ground truth)
#
# ## Key Metrics
# - Expected Calibration Error (ECE)
# - Brier Score
# - Wager-Weighted Accuracy (novel — exponential penalty for confident wrong answers)
# - Difficulty-Stratified analysis (reveals Dunning-Kruger pattern)

# %%
import kaggle_benchmarks as kbench
import numpy as np
from dataclasses import dataclass

# %%
@dataclass
class VulnResponse:
    severity_or_answer: str
    explanation: str
    confidence: float
    wager: int
    reasoning: str

@dataclass
class RiskFactorResponse:
    assessment: str
    rationale: str
    confidence: float
    wager: int
    reasoning: str

# %%
# === Cybersecurity Vulnerability Assessment Items ===

CYBER_ITEMS = [
    # Tier 1: TRIVIAL
    {"id": "cyber_mc1_001", "difficulty": 1, "type": "attack_identification",
     "prompt": """A user reports an email from security-team@g00gle-verify.com (zeros instead of o's), subject "Urgent: Your account will be suspended in 24 hours." SPF: FAIL, DKIM: NONE, DMARC: FAIL. Reply-To: totallylegit8847@protonmail.com. Link goes to http://g00gle-verify.com/login.\n\nClassify this email: Legitimate, Phishing, Spam, or Graymail.""",
     "correct": "phishing"},
    {"id": "cyber_mc1_002", "difficulty": 1, "type": "vuln_severity",
     "prompt": """A network scan finds an internet-facing Cisco router admin panel accessible via HTTP (not HTTPS) on port 80 at a 50-person branch office. Default credentials work: admin/admin. The router handles all traffic including VPN tunnels to the corporate data center.\n\nRate severity: Informational, Low, Medium, High, or Critical.""",
     "correct": "critical"},

    # Tier 2: EASY
    {"id": "cyber_mc1_003", "difficulty": 2, "type": "cve_assessment",
     "prompt": """Vulnerability scanner flags CVE-2021-44228 (Log4Shell) on an internal Java app. pom.xml shows log4j-core 2.14.1. The code does Logger.info("User submitted: " + userInput) where userInput comes from a web form. Server has outbound internet access.\n\nIs this vulnerable, and what severity: Not Vulnerable, Low, Medium, High, or Critical?""",
     "correct": "critical"},
    {"id": "cyber_mc1_004", "difficulty": 2, "type": "attack_identification",
     "prompt": """A web app on AWS EC2 has a "link preview" feature. A pentester submits: http://169.254.169.254/latest/meta-data/iam/security-credentials/ — the app returns valid AWS IAM temporary credentials (AccessKeyId, SecretAccessKey, Token).\n\nIdentify the vulnerability type and severity: Informational, Low, Medium, High, or Critical.""",
     "correct": "critical"},

    # Tier 3: MEDIUM
    {"id": "cyber_mc1_005", "difficulty": 3, "type": "vuln_severity",
     "prompt": """A Java web app uses Apache Commons Collections 3.2.1. Code review finds: ObjectInputStream ois = new ObjectInputStream(request.getInputStream()); Object obj = ois.readObject(); — the endpoint requires JWT auth but is accessible to all 12,000 users. Server has network access to internal DB and message queue.\n\nRate severity: Informational, Low, Medium, High, or Critical.""",
     "correct": "critical"},
    {"id": "cyber_mc1_006", "difficulty": 3, "type": "vuln_severity",
     "prompt": """DNS record found: staging-api.company.com CNAME company-staging.herokuapp.com. The Heroku app is deleted (NXDOMAIN). The main domain has: wildcard SSL cert (*.company.com), CORS policy allowing *.company.com, and session cookies set with Domain=.company.com.\n\nRate the subdomain takeover severity: Informational, Low, Medium, High, or Critical.""",
     "correct": "high"},

    # Tier 4: HARD
    {"id": "cyber_mc1_007", "difficulty": 4, "type": "vuln_severity",
     "prompt": """A researcher reports a race condition in OAuth 2.0 authorization code flow. In a ~50ms window, duplicate requests with the same auth code can link User B's session to User A's token. Reproduced 5% of the time with 20 concurrent requests. BUT: auth codes are 128-bit hex with 60-second expiry, and PKCE is used (race occurs after PKCE validation). The attacker needs the victim's exact code.\n\nRate severity: Informational, Low, Medium, High, or Critical.""",
     "correct": "low"},
    {"id": "cyber_mc1_008", "difficulty": 4, "type": "cve_assessment",
     "prompt": """Cloud provider notifies you of a new Spectre-variant side-channel on your Intel Xeon multi-tenant VMs. PoC extracts 1 byte per 30 seconds from adjacent VM memory. Your environment: 14 AWS EC2 m6i.xlarge (shared hardware), processes PCI cardholder data and HIPAA PHI. AWS will patch microcode in 72 hours (3-8% perf hit). Options: (A) dedicated hosts +$4,200/mo, (B) wait for patch, (C) accept risk, (D) shut down.\n\nWhat is the actual risk level: Negligible, Low, Medium, High, or Critical?""",
     "correct": "low"},

    # Tier 5: NEAR-IMPOSSIBLE
    {"id": "cyber_mc1_009", "difficulty": 5, "type": "vuln_severity",
     "prompt": """A paper describes: JS-based Rowhammer → bit flips in DRAM rows adjacent to SGX enclave pages → side channel via SGX abort/no-abort to extract enclave contents. Demonstrated RSA key extraction in 3.5 hours on Skylake + single-rank DDR4-2133 + TRR disabled. YOUR servers: Ice Lake CPUs (updated microcode), DDR4-3200 dual-rank ECC with TRR enabled, SGX enclaves for payment keys. Also runs Node.js with vm2 sandbox processing untrusted user JS templates.\n\nRate exploitability in YOUR environment: Negligible, Low, Medium, High, or Critical.""",
     "correct": "low"},
    {"id": "cyber_mc1_010", "difficulty": 5, "type": "attack_identification",
     "prompt": """Attack chain reported: (1) "website screenshot" feature runs user URLs in headless Puppeteer; (2) attacker uses DNS rebinding (TTL=0) to redirect same-origin requests to 10.96.0.1 (K8s API); (3) Chrome's --allow-file-access-from-files flag lets JS read /var/run/secrets/kubernetes.io/serviceaccount/token; (4) service account has cluster-admin. What is the PRIMARY root cause and single most effective mitigation?\n\nA. DNS rebinding — implement DNS pinning\nB. Overprivileged service account — reduce RBAC\nC. Chrome misconfiguration — remove file access flag\nD. Network policy gap — block pod-to-API traffic\nE. Multiple compounding — no single fix sufficient""",
     "correct": "b"},
    # ── D1 (Trivial) ─────────────────────────────────────────────────────
    {
        "id": "cyber_mc1_011",
        "scenario_type": "vuln_severity",
        "difficulty": 1,
        "scenario": """A vulnerability scan of an internet-facing Apache web server reveals it is running version 2.4.49. The server hosts a public marketing website with no authentication. The scan flags CVE-2021-41773, a path traversal vulnerability that allows reading arbitrary files outside the document root via crafted URL paths such as /cgi-bin/.%2e/.%2e/etc/passwd. The mod_cgi module is enabled, which means the path traversal can also be leveraged for remote code execution. The server runs as the 'www-data' user with access to application configuration files containing database credentials.""",
        "question": "What is the severity of CVE-2021-41773 on this server: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "CVE-2021-41773 with mod_cgi enabled allows unauthenticated remote code execution on an internet-facing server, making it critical severity.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_012",
        "scenario_type": "attack_identification",
        "difficulty": 1,
        "scenario": """An employee at a mid-size company receives an SMS message claiming to be from the IT helpdesk: 'Your corporate VPN certificate expires today. Renew immediately at https://vpn-renew-corp.xyz/update or lose access.' The employee clicks the link and enters their Active Directory username, password, and MFA code on a page that looks identical to the company's real VPN portal. Twenty minutes later, the SOC detects a successful VPN login from an IP address in a foreign country using the employee's credentials.""",
        "question": "What type of attack is this: Phishing, Smishing, Vishing, Credential Stuffing, or Brute Force?",
        "correct_answer": "smishing",
        "explanation": "This is smishing (SMS phishing) — a social engineering attack delivered via text message that tricks the victim into entering credentials on a fake site.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_013",
        "scenario_type": "vuln_severity",
        "difficulty": 1,
        "scenario": """During a routine audit of a company's AWS S3 buckets, a security analyst discovers that the bucket 'company-customer-backups' has its ACL set to 'public-read'. The bucket contains nightly database exports of the customer management system including full names, email addresses, phone numbers, billing addresses, and the last four digits of credit cards. The bucket has been public for approximately 90 days. CloudTrail logs show 14 unique external IP addresses have performed ListObjects and GetObject operations on the bucket over the past month.""",
        "question": "Rate the severity of this misconfiguration: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "A publicly readable S3 bucket containing PII with evidence of external access is a critical data breach requiring immediate remediation and likely regulatory notification.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_014",
        "scenario_type": "cve_assessment",
        "difficulty": 1,
        "scenario": """A vulnerability scanner flags CVE-2017-0144 (EternalBlue) on three Windows Server 2012 R2 machines in a hospital network. These servers run the hospital's electronic health records (EHR) system and are accessible from the internal network. SMBv1 is enabled. The servers have not been patched since 2019 due to vendor certification requirements. The network is flat with no segmentation between clinical workstations and these servers. The hospital has 2,000 employees with network access.""",
        "question": "Is this vulnerability exploitable and what is the severity: Not Vulnerable, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "EternalBlue on unpatched SMBv1 servers on a flat network is trivially exploitable for remote code execution and was the vector for WannaCry/NotPetya; this is critical.",
        "domain": "cybersecurity",
    },

    # ── D2 (Easy) ─────────────────────────────────────────────────────────
    {
        "id": "cyber_mc1_015",
        "scenario_type": "vuln_severity",
        "difficulty": 2,
        "scenario": """A penetration tester finds a reflected XSS vulnerability on an e-commerce platform's search page. Injecting <script>alert(document.cookie)</script> via the 'q' parameter executes in the victim's browser. The application uses session cookies without the HttpOnly flag, meaning JavaScript can read them. The site processes credit card payments directly (not via iframe/redirect to a payment processor). CSP headers are not implemented. The site has 500,000 monthly active users.""",
        "question": "Rate the severity of this XSS vulnerability: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "high",
        "explanation": "Reflected XSS with cookie theft capability on a payment-processing site is high severity; it enables session hijacking and potential payment data theft, though it requires user interaction (clicking a crafted link).",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_016",
        "scenario_type": "attack_identification",
        "difficulty": 2,
        "scenario": """A web application firewall logs show repeated POST requests to /api/login from 12,000 unique IP addresses over 6 hours. Each IP makes only 3-5 requests. The payloads contain different username/password combinations — none appear to be sequential or dictionary-based. Cross-referencing the credentials with known breach databases (Have I Been Pwned), 94% of the attempted username/email and password pairs appear in previous data breaches from other services. The application does not enforce rate limiting per account, only per IP.""",
        "question": "What type of attack is this: Brute Force, Password Spraying, Credential Stuffing, Dictionary Attack, or Rainbow Table Attack?",
        "correct_answer": "credential stuffing",
        "explanation": "The use of known breach credentials from other services across distributed IPs is the hallmark of credential stuffing, which exploits password reuse across sites.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_017",
        "scenario_type": "cve_assessment",
        "difficulty": 2,
        "scenario": """A security team is assessing CVE-2023-23397 (Microsoft Outlook NTLM relay) in their environment. The vulnerability allows an attacker to send a specially crafted email with a UNC path that triggers NTLM authentication to an attacker-controlled server — no user interaction beyond receiving the email in Outlook is required. The organization uses Microsoft 365 with on-premises Exchange hybrid, Outlook desktop client on all 3,000 workstations, and NTLM is still enabled for legacy application compatibility. Outbound SMB (port 445) is blocked at the perimeter firewall, but outbound to arbitrary ports above 1024 is allowed.""",
        "question": "Is this vulnerability exploitable in this environment and what is the severity: Not Vulnerable, Low, Medium, High, or Critical?",
        "correct_answer": "high",
        "explanation": "While outbound SMB is blocked, the attacker can use a high-numbered port for the NTLM relay since outbound traffic above 1024 is allowed. Zero-click NTLM hash capture makes this high severity, though exploitation requires the attacker to set up a receiving server.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_018",
        "scenario_type": "vuln_severity",
        "difficulty": 2,
        "scenario": """A code review of a Django web application reveals the following pattern in multiple views: query = "SELECT * FROM products WHERE category = '" + request.GET['cat'] + "'" followed by cursor.execute(query). The application uses PostgreSQL 14 as its backend. The database user has SELECT, INSERT, UPDATE, and DELETE privileges on all application tables but no SUPERUSER or FILE privileges. The application is behind Cloudflare WAF with the OWASP Core Rule Set enabled.""",
        "question": "Rate the severity of this SQL injection: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "high",
        "explanation": "Classic string concatenation SQL injection is high severity even with a WAF (which can be bypassed) — the attacker can read/modify all application data. It's not critical because the DB user lacks SUPERUSER/FILE privileges, limiting OS-level impact.",
        "domain": "cybersecurity",
    },

    # ── D3 (Medium) ───────────────────────────────────────────────────────
    {
        "id": "cyber_mc1_019",
        "scenario_type": "cve_assessment",
        "difficulty": 3,
        "scenario": """Your organization runs a Kubernetes cluster (v1.27) on GKE. A vulnerability scanner flags CVE-2022-0185 (heap overflow in Linux kernel's filesystem context handling) on all nodes running kernel 5.15.x. The CVE allows container escape via CAP_SYS_ADMIN. Your cluster configuration: all pods run with securityContext.allowPrivilegeEscalation: false, no pods have CAP_SYS_ADMIN (dropped by default PodSecurityPolicy), GKE Sandbox (gVisor) is enabled on the node pool running untrusted workloads, but the main application node pool uses standard containerd runtime. Binary Authorization is enforced.""",
        "question": "Is CVE-2022-0185 exploitable in this environment: Not Vulnerable, Low, Medium, High, or Critical?",
        "correct_answer": "low",
        "explanation": "The exploit requires CAP_SYS_ADMIN which is dropped by the PodSecurityPolicy, and allowPrivilegeEscalation is false. Without this capability, the heap overflow cannot be triggered from within containers, making practical exploitation very unlikely in this hardened configuration.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_020",
        "scenario_type": "attack_identification",
        "difficulty": 3,
        "scenario": """A SOC analyst notices that a developer's workstation is making unusual DNS queries: sequential queries to abc123.data.evil-c2.com, def456.data.evil-c2.com, ghi789.data.evil-c2.com — each subdomain label is a 32-character hex string. The queries occur every 5 seconds in bursts of 20, then pause for 10 minutes. Total unique subdomain queries: ~4,000 over 8 hours. The workstation recently cloned a public GitHub repository containing a compromised npm dependency. No HTTP/HTTPS traffic to evil-c2.com is observed. Internal DNS resolvers forward these queries upstream. The organization does not perform DNS-layer filtering or TLS inspection on DNS-over-HTTPS.""",
        "question": "What is the primary technique being used: DNS Tunneling, DNS Beaconing, Domain Generation Algorithm (DGA), DNS Cache Poisoning, or Fast Flux DNS?",
        "correct_answer": "dns tunneling",
        "explanation": "The hex-encoded subdomain labels carrying data in sequential bursts with no corresponding HTTP traffic is classic DNS tunneling (data exfiltration over DNS). Beaconing would involve repeated queries to the same domain for C2 check-in, not data-carrying subdomains.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_021",
        "scenario_type": "vuln_severity",
        "difficulty": 3,
        "scenario": """A smart building management system (BMS) from vendor Acme Controls runs on an embedded Linux device. Firmware analysis reveals: (1) a hardcoded SSH key pair shared across all units of this model, (2) the management web interface on port 443 with a self-signed cert and no CSRF protection, (3) an undocumented REST API endpoint /api/v1/firmware/upload with no authentication. The BMS controls HVAC, lighting, and physical access control (door locks) for a 40-story commercial office building. The BMS is on a separate VLAN but the VLAN is routable from the corporate network (no ACLs). There are 200 employees on the corporate network.""",
        "question": "Rate the overall severity of these findings: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "Unauthenticated firmware upload on a physical access control system reachable from the corporate network is critical — an attacker could upload malicious firmware to control door locks and HVAC, creating both cyber and physical safety risks.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_022",
        "scenario_type": "cve_assessment",
        "difficulty": 3,
        "scenario": """A telecom company uses SolarWinds Orion for network monitoring. After the SUNBURST supply chain attack disclosure (CVE-2020-14005 and related), they check their environment. Their Orion server is version 2020.2.1 HF1 (a known compromised version). However, the Orion server is on an isolated management network with no direct internet access — all updates were applied via USB from an air-gapped staging server. DNS logs from the management network's internal resolver show NO queries to avsvmcloud.com or any other known SUNBURST DGA domains. The management network firewall logs confirm zero outbound connections to external IPs from the Orion server in the past 14 months.""",
        "question": "Was this Orion instance likely compromised by SUNBURST: Yes (active compromise) or No (backdoor present but not activated)?",
        "correct_answer": "no",
        "explanation": "While the backdoor DLL was present in the compromised build, SUNBURST required DNS resolution to avsvmcloud.com to activate and receive C2 instructions. The air-gapped network with no outbound DNS/internet access prevented activation, so the backdoor was dormant.",
        "domain": "cybersecurity",
    },

    # ── D4 (Hard) ─────────────────────────────────────────────────────────
    {
        "id": "cyber_mc1_023",
        "scenario_type": "vuln_severity",
        "difficulty": 4,
        "scenario": """A security researcher discovers that a popular password manager's browser extension implements its autofill logic by injecting content scripts into all web pages. The content script searches the DOM for input fields with type="password" and fills credentials for matching URLs. The URL matching uses: scheme + hostname + port. However, the researcher finds the extension also fills credentials on pages loaded inside an <iframe> if the iframe's src matches the saved URL, even when the parent page is on a different origin. The extension has 8 million users. The autofill triggers automatically on page load without user interaction. The extension does NOT check X-Frame-Options or CSP frame-ancestors of the target site.""",
        "question": "Rate the severity of this autofill-in-iframe behavior: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "high",
        "explanation": "An attacker can embed a legitimate login page in a transparent iframe on a malicious site, have the extension auto-fill credentials, then use JavaScript postMessage or timing side-channels to exfiltrate them. This affects 8M users but requires the target site to be frameable (many banking sites set X-Frame-Options), limiting it from critical to high.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_024",
        "scenario_type": "attack_identification",
        "difficulty": 4,
        "scenario": """An incident responder finds the following artifacts on a compromised Linux server: (1) A modified /usr/lib/x86_64-linux-gnu/security/pam_unix.so — the hash differs from the package version but the file size is identical (padding adjusted). (2) Strings analysis of the modified PAM module reveals an embedded hardcoded hash that doesn't correspond to any system user. (3) /var/log/auth.log shows successful 'su' authentications for multiple users with no corresponding 'session opened' entries from sshd or other login services. (4) The modification timestamp on pam_unix.so was preserved using touch --reference. (5) The server's package manager (dpkg) reports the file as unmodified because the attacker also updated /var/lib/dpkg/info/libpam-modules:amd64.md5sums.""",
        "question": "What persistence technique is this: Rootkit, PAM Backdoor, LD_PRELOAD Hijacking, Cron Persistence, or SSH Authorized Keys?",
        "correct_answer": "pam backdoor",
        "explanation": "The modified pam_unix.so with an embedded hardcoded hash is a PAM backdoor — it accepts the attacker's universal password for any account while passing legitimate auth through. The attacker preserved timestamps and updated dpkg checksums for anti-forensics.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_025",
        "scenario_type": "cve_assessment",
        "difficulty": 4,
        "scenario": """A medical device manufacturer assesses CVE-2020-0601 (CurveBall/Chain of Fools — Windows CryptoAPI ECC spoofing) for their FDA-regulated devices. The vulnerability allows spoofing ECC certificate chains by crafting a root CA cert with the same public key but attacker-chosen parameters. Their environment: 2,500 bedside patient monitors running Windows 10 IoT Enterprise LTSC 2019 (unpatched — FDA change control). The monitors validate drug library updates via Authenticode signatures using ECC certificates. Updates are delivered over the hospital's Wi-Fi network (WPA2-Enterprise). Monitors do not have internet access but receive updates from an internal WSUS-like distribution server. A compromised drug library could alter dosage limits.""",
        "question": "Rate the severity of CurveBall for these specific devices: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "CurveBall allows an attacker on the hospital network to forge Authenticode signatures on malicious drug library updates, potentially altering medication dosage limits on 2,500 patient monitors — a direct patient safety risk. The internal network delivery and lack of patching make this critical despite requiring network access.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_026",
        "scenario_type": "vuln_severity",
        "difficulty": 4,
        "scenario": """A researcher finds that a widely-used TLS library (used by ~15% of IoT devices) implements ECDSA signature verification with a subtle flaw: it does not check that the signature values (r, s) are within the valid range [1, n-1] where n is the curve order. Instead, it accepts r=0 or s=0. Additionally, the library's point multiplication routine returns the point at infinity for a zero scalar. This means an attacker can forge a valid-looking signature for ANY message by submitting (r=0, s=any_value) or (r=any_value, s=0). The library is used for firmware update verification and mutual TLS authentication on industrial control systems. The vendor claims the risk is mitigated because 'attackers would need network access to the ICS network.'""",
        "question": "Rate the severity of this cryptographic implementation flaw: Informational, Low, Medium, High, or Critical?",
        "correct_answer": "critical",
        "explanation": "A trivially exploitable ECDSA signature bypass (null signature forgery) that affects firmware verification and mTLS on ICS devices is critical. The vendor's mitigation claim is insufficient — network access to ICS is routinely obtained in targeted attacks, and the flaw enables complete authentication bypass and malicious firmware installation.",
        "domain": "cybersecurity",
    },

    # ── D5 (Near-Impossible) ──────────────────────────────────────────────
    {
        "id": "cyber_mc1_027",
        "scenario_type": "attack_identification",
        "difficulty": 5,
        "scenario": """A nation-state incident response team discovers the following during forensic analysis of a diplomatic network: (1) Encrypted TLS traffic from a workstation to a legitimate, high-traffic CDN (Cloudflare) shows unusual patterns — every 30 seconds, an HTTPS request is made whose encrypted payload size modulo 64 cycles through a pattern that, when decoded, maps to ASCII characters. (2) The workstation's RAM dump reveals a process injected into explorer.exe that reads keystrokes, encrypts them with a static AES-256 key, and encodes them into the Content-Length variation of HTTP requests to blog.legitimate-news-site.com (which is behind Cloudflare). (3) The C2 responses are encoded in the TLS session ticket size variation of the server's responses. (4) No custom DNS, no beaconing to unusual domains, no anomalous destination IPs — all traffic goes to Cloudflare's IP ranges. (5) The malware binary is fileless — decrypted in memory from Windows registry values stored as REG_BINARY under HKCU\Software\Classes\CLSID.""",
        "question": "What covert channel technique is primarily being used for C2: Domain Fronting, Steganography in TLS Metadata, DNS over HTTPS tunneling, Protocol-level Steganography via Traffic Shaping, or Dead Drop via Cloud Storage?",
        "correct_answer": "protocol-level steganography via traffic shaping",
        "explanation": "The malware encodes data in the modulated sizes of legitimate HTTPS payloads and reads responses from TLS session ticket size variations — this is protocol-level steganography embedded in traffic shaping, not domain fronting (which uses Host header manipulation) or traditional steganography (which hides data in images/files).",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_028",
        "scenario_type": "cve_assessment",
        "difficulty": 5,
        "scenario": """A semiconductor company discovers a vulnerability in their custom RISC-V processor's speculative execution engine. The processor implements a branch target buffer (BTB) that is indexed by virtual address bits [11:2] without including the ASID (Address Space Identifier). This means two processes with different ASIDs but overlapping virtual addresses will share BTB entries. A researcher demonstrates that by training the BTB from an unprivileged process, they can mistrain branch prediction in the kernel's syscall handler, causing speculative execution of a gadget at a kernel virtual address that transiently loads data from an attacker-controlled address into the L1 data cache. The transient load bypasses PMP (Physical Memory Protection) checks because PMP is only enforced at commit, not during speculation. Cache timing reveals the loaded byte. The attack extracts kernel memory at ~500 bytes/second. The processor is used in automotive ECUs running safety-critical ASIL-D applications with shared memory between RTOS partitions.""",
        "question": "Is this primarily a Spectre-BTB (v2), Meltdown, Spectre-RSB, Spectre-STL (v4), or novel microarchitectural class of vulnerability?",
        "correct_answer": "spectre-btb",
        "explanation": "This is a Spectre-BTB (variant 2) attack — the core mechanism is BTB poisoning across privilege boundaries due to missing ASID tagging, causing speculative execution at attacker-controlled targets. The PMP bypass during speculation is a consequence of the transient execution, not a separate vulnerability class like Meltdown (which exploits lazy exception handling).",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_029",
        "scenario_type": "vuln_severity",
        "difficulty": 5,
        "scenario": """A research team discovers that a post-quantum key encapsulation mechanism (KEM) implementation — specifically CRYSTALS-Kyber (ML-KEM) as standardized in FIPS 203 — in a widely-deployed HSM contains a timing side channel. The decapsulation operation's execution time varies by ~200 nanoseconds depending on whether the re-encryption check (Fujisaki-Okamoto transform) succeeds or fails. This is because the constant-time comparison function uses a CMOV instruction that, on this specific HSM's ARM Cortex-A72 processor, has data-dependent timing when operating on values that cross a cache line boundary. The HSM is used for TLS 1.3 key exchange (hybrid X25519+ML-KEM-768) at a financial institution processing 50,000 TLS handshakes per second. An attacker with network access can submit chosen ciphertexts and measure response times. Academic papers suggest that Kyber's FO transform requires approximately 2^20 adaptive chosen ciphertext queries with ~1-bit timing leakage per query to recover a session key.""",
        "question": "Rate the practical exploitability of this timing side channel over a network: Negligible, Low, Medium, High, or Critical?",
        "correct_answer": "low",
        "explanation": "While the timing vulnerability is real, the ~200ns difference is extremely difficult to measure over a network (where jitter is typically microseconds to milliseconds). The 2^20 queries needed for key recovery would take significant time and the hybrid scheme means X25519 must also be broken. Practical network exploitation is low, though local/co-located attackers face a higher risk.",
        "domain": "cybersecurity",
    },
    {
        "id": "cyber_mc1_030",
        "scenario_type": "attack_identification",
        "difficulty": 5,
        "scenario": """During an audit of a 5G core network (standalone architecture, Release 16), a security team discovers anomalous behavior in the Network Repository Function (NRF). The NRF's OAuth2 token issuance shows that a rogue Network Function (NF) has registered itself as an SMF (Session Management Function) using a valid but stolen NF instance certificate. The rogue SMF has been: (1) requesting OAuth2 tokens from the NRF with scope 'nsmf-pdusession' — which the NRF grants because the certificate's NF type matches; (2) using those tokens to query the UDM (Unified Data Management) for subscriber profiles via Nudm_SDM service; (3) issuing PDU session modification requests to legitimate UPFs (User Plane Functions) to redirect user traffic through an attacker-controlled data network. The rogue NF communicates over the legitimate SBI (Service Based Interface) using HTTP/2 over TLS 1.3 with valid mTLS certificates. All traffic appears legitimate to the SBI proxy.""",
        "question": "What is the PRIMARY vulnerability class being exploited: NF Impersonation via Certificate Compromise, OAuth Scope Over-Privilege, SBI API Authorization Bypass, GTP Tunnel Manipulation, or SUPI/SUCI Correlation Attack?",
        "correct_answer": "nf impersonation via certificate compromise",
        "explanation": "The root cause is NF impersonation using a stolen certificate — the rogue NF convincingly poses as a legitimate SMF because 5G SBI authorization relies on NF type in the certificate for OAuth scope grants. The OAuth and API access follow naturally from the successful impersonation; they are consequences, not the primary vulnerability.",
        "domain": "cybersecurity",
    },
]

# === Risk Factor Items (Finance Domain) ===

RF_ITEMS = [
    {"id": "rf_001", "company": "Silicon Valley Bank (SIVB)", "sector": "Regional Banking", "year": 2022,
     "risk": "We are subject to interest rate risk. Rapid rate increases could cause significant unrealized losses on our $91.3B held-to-maturity portfolio. A large proportion of deposits are uninsured and from concentrated tech/VC sectors.",
     "materialized": True, "difficulty": 1},
    {"id": "rf_002", "company": "Pfizer (PFE)", "sector": "Pharmaceuticals", "year": 2022,
     "risk": "Revenue from COVID-19 vaccine and antiviral may decline significantly as the pandemic transitions to endemic phase. Demand is dependent on government purchasing, variants, and vaccination rates.",
     "materialized": True, "difficulty": 2},
    {"id": "rf_003", "company": "Tesla (TSLA)", "sector": "Automotive", "year": 2022,
     "risk": "Increasing competition in EVs from traditional automakers and new entrants could adversely affect market share, pricing, and margins. We may need to reduce prices to maintain demand.",
     "materialized": True, "difficulty": 3},
    {"id": "rf_004", "company": "NVIDIA (NVDA)", "sector": "Semiconductors", "year": 2022,
     "risk": "U.S. export controls restricting sales of advanced AI chips to China could materially impact revenue. China represented ~22% of data center revenue.",
     "materialized": False, "difficulty": 4},
    {"id": "rf_005", "company": "CrowdStrike (CRWD)", "sector": "Cybersecurity", "year": 2023,
     "risk": "Our Falcon platform operates at the kernel level. Errors or defects in software updates could cause widespread system disruptions, resulting in significant reputational harm and legal liability.",
     "materialized": True, "difficulty": 5},
    # ── D1 (Trivial / Obvious) ───────────────────────────────────────────
    {
        "id": "rf_006",
        "scenario_type": "risk_factor",
        "difficulty": 1,
        "scenario": """FTX Trading Ltd (2021 10-K equivalent / investor disclosures): 'Customer assets may be used for proprietary trading and lending operations by affiliated entities. Alameda Research, a related party, may receive preferential treatment including credit lines collateralized by FTT tokens. There is no independent board oversight of related-party transactions. Commingling of customer funds with proprietary trading creates concentration risk.' FTX reported holding $16 billion in customer deposits with Alameda Research listed as both a counterparty and borrower. No independent audit had been completed.""",
        "question": "Did the commingling of customer funds with Alameda Research materially impact FTX within 18 months?",
        "correct_answer": "yes",
        "explanation": "FTX filed for Chapter 11 bankruptcy in November 2022 after it was revealed that approximately $8 billion in customer funds had been diverted to Alameda Research, which suffered massive trading losses.",
        "domain": "finance",
    },
    {
        "id": "rf_007",
        "scenario_type": "risk_factor",
        "difficulty": 1,
        "scenario": """Bed Bath & Beyond (BBBY) 10-K FY2021 (filed April 2022): 'We have experienced significant declines in comparable store sales and customer traffic. Our turnaround strategy requires substantial capital investment while we face $1.4 billion in long-term debt. Cash and cash equivalents were $439 million at year-end, down from $1.1 billion the prior year. Our ABL credit facility of $1 billion has borrowing base limitations tied to inventory levels, which are declining. We may be unable to maintain compliance with financial covenants.' The company's stock had declined 65% over the prior 12 months, and same-store sales had fallen for six consecutive quarters.""",
        "question": "Did the liquidity and debt servicing risk materially impact Bed Bath & Beyond within 18 months?",
        "correct_answer": "yes",
        "explanation": "Bed Bath & Beyond filed for Chapter 11 bankruptcy in April 2023 after failing to restructure its debt, burning through remaining cash, and being unable to draw on its credit facility due to collapsing inventory and revenue.",
        "domain": "finance",
    },
    {
        "id": "rf_008",
        "scenario_type": "risk_factor",
        "difficulty": 1,
        "scenario": """Credit Suisse Group AG (2021 Annual Report): 'We are subject to significant litigation, regulatory proceedings, and government investigations that may result in material losses. We recorded CHF 4.4 billion in litigation provisions. The Archegos Capital Management and Greensill Capital events resulted in combined losses exceeding CHF 5.5 billion and significant reputational damage. Ongoing client asset outflows in our wealth management business could accelerate if confidence is not restored. We face potential credit rating downgrades.' The bank had already experienced net outflows of CHF 13.4 billion in Q4 2021.""",
        "question": "Did the reputational damage and client outflow risk materially impact Credit Suisse within 18 months?",
        "correct_answer": "yes",
        "explanation": "Credit Suisse experienced accelerating client outflows of CHF 110+ billion in Q4 2022, a collapsing share price, and was forced into an emergency acquisition by UBS in March 2023 at a 59% discount, effectively ceasing to exist as an independent entity.",
        "domain": "finance",
    },

    # ── D2 (Easy) ─────────────────────────────────────────────────────────
    {
        "id": "rf_009",
        "scenario_type": "risk_factor",
        "difficulty": 2,
        "scenario": """Coinbase Global (COIN) 10-K FY2021 (filed February 2022): 'A significant portion of our net revenue is derived from transaction fees on our platform, which are directly tied to crypto asset trading volumes and prices. Bitcoin and Ethereum accounted for approximately 42% of total trading volume. Our revenue is highly correlated with the market price of crypto assets. A sustained decline in crypto prices could materially reduce trading volume and transaction revenue.' In Q4 2021, Coinbase reported $2.5 billion in net revenue driven by record crypto trading volumes during the bull market, with Bitcoin near its all-time high of $69,000.""",
        "question": "Did the crypto price decline risk materially impact Coinbase's revenue within 18 months?",
        "correct_answer": "yes",
        "explanation": "Bitcoin fell from ~$69K to ~$16K by late 2022. Coinbase's quarterly revenue dropped from $2.5B (Q4 2021) to $605M (Q4 2022), a 76% decline, and the company laid off 20% of its workforce in June 2022.",
        "domain": "finance",
    },
    {
        "id": "rf_010",
        "scenario_type": "risk_factor",
        "difficulty": 2,
        "scenario": """Meta Platforms (META) 10-K FY2021 (filed February 2022): 'Apple's iOS changes, including App Tracking Transparency (ATT), have and may continue to adversely impact our advertising targeting and measurement capabilities. We believe these changes contributed to advertising headwinds in the second half of 2021. Additionally, competitive pressure from short-form video platforms (particularly TikTok) may reduce time spent on our platforms by younger demographics.' Meta reported $117.9 billion in 2021 advertising revenue and noted that ATT had begun affecting advertiser ROI measurement.""",
        "question": "Did Apple's ATT privacy changes materially impact Meta's advertising revenue within 18 months?",
        "correct_answer": "yes",
        "explanation": "Meta reported its first-ever year-over-year revenue decline in Q2 2022, directly attributing approximately $10 billion in annualized revenue loss to Apple's ATT changes. The stock fell 64% from its peak through October 2022.",
        "domain": "finance",
    },
    {
        "id": "rf_011",
        "scenario_type": "risk_factor",
        "difficulty": 2,
        "scenario": """Carvana Co. (CVNA) 10-K FY2021 (filed February 2022): 'We have a history of losses and may not achieve or maintain profitability. Net loss was $287 million in 2021. Our growth strategy requires significant capital expenditure for inspection/reconditioning centers and inventory acquisition. Total debt is $6.6 billion. Rising interest rates could increase our cost of capital and reduce consumer demand for auto loans. Our unit economics depend on the ability to acquire, recondition, and sell vehicles at volumes that generate positive gross profit per unit.' Carvana had grown retail units sold 74% year-over-year in 2021, funded by aggressive debt issuance.""",
        "question": "Did rising interest rates and the debt burden materially impact Carvana within 18 months?",
        "correct_answer": "yes",
        "explanation": "As interest rates rose sharply in 2022, used car demand fell, Carvana's GPU turned negative, and the stock fell 98% from its peak. The company nearly defaulted on its $6.6B debt, requiring a distressed debt exchange in late 2022/early 2023.",
        "domain": "finance",
    },

    # ── D3 (Medium) ───────────────────────────────────────────────────────
    {
        "id": "rf_012",
        "scenario_type": "risk_factor",
        "difficulty": 3,
        "scenario": """Evergrande Group (2020 Annual Report): 'We have significant offshore US dollar-denominated debt obligations totaling approximately $20 billion. Our ability to service these obligations depends on our continued ability to sell residential properties at projected volumes and prices. A slowdown in China's property market or regulatory restrictions on developer leverage (including the "Three Red Lines" policy) could constrain our liquidity. Cross-default provisions in our bond indentures mean that a default on any single obligation could trigger acceleration of all outstanding debt.' Evergrande's total liabilities stood at approximately $300 billion, with contracted sales still growing 8% year-over-year.""",
        "question": "Did the regulatory leverage restrictions and liquidity risk materially impact Evergrande within 18 months?",
        "correct_answer": "yes",
        "explanation": "Evergrande defaulted on its offshore US dollar bonds in December 2021 after the Three Red Lines policy restricted its ability to take on new debt, triggering a liquidity crisis. The company's Hong Kong-listed shares were eventually suspended and a liquidation order was issued in January 2024.",
        "domain": "finance",
    },
    {
        "id": "rf_013",
        "scenario_type": "risk_factor",
        "difficulty": 3,
        "scenario": """Zoom Video Communications (ZM) 10-K FY2022 (filed March 2022): 'The COVID-19 pandemic significantly accelerated adoption of our platform. As the pandemic subsides and in-person activities resume, customers may reduce usage or fail to renew subscriptions. Net revenue growth decelerated from 326% in FY2021 to 55% in FY2022. We face intensifying competition from Microsoft Teams (bundled with Microsoft 365), Google Meet, and Cisco Webex, who can offer video conferencing at minimal incremental cost to existing enterprise customers.' Zoom had 509,800 enterprise customers and reported $4.1 billion in FY2022 revenue.""",
        "question": "Did the post-pandemic demand normalization and competitive pressure materially impact Zoom within 18 months?",
        "correct_answer": "yes",
        "explanation": "Zoom's revenue growth decelerated to near-zero by FY2023 (ending Jan 2023), enterprise customer growth stalled, and the stock declined ~80% from its 2021 peak as the return-to-office trend and Teams competition eroded its dominance.",
        "domain": "finance",
    },
    {
        "id": "rf_014",
        "scenario_type": "risk_factor",
        "difficulty": 3,
        "scenario": """Silvergate Capital (SI) 10-K FY2021 (filed March 2022): 'Our Silvergate Exchange Network (SEN) and digital asset customer deposits create concentration risk in the cryptocurrency industry. Digital asset customer deposits were $14.1 billion at year-end, representing 92% of total deposits. These deposits are non-interest-bearing and highly volatile, as they fluctuate with crypto market conditions. A significant crypto market downturn or the failure of a major digital asset customer could result in rapid, large-scale deposit withdrawals.' Silvergate was the primary banking partner for numerous major crypto firms including FTX and Alameda Research.""",
        "question": "Did the crypto industry concentration risk materially impact Silvergate within 18 months?",
        "correct_answer": "yes",
        "explanation": "Following the FTX collapse in November 2022, Silvergate experienced a bank run with $8.1 billion in deposit withdrawals in Q4 2022 (over 68% of digital asset deposits), was forced to sell securities at a $718M loss, and voluntarily liquidated in March 2023.",
        "domain": "finance",
    },

    # ── D4 (Hard / Counterintuitive) ──────────────────────────────────────
    {
        "id": "rf_015",
        "scenario_type": "risk_factor",
        "difficulty": 4,
        "scenario": """Apple Inc. (AAPL) 10-K FY2022 (filed October 2022): 'Our products and services may be subject to government regulations and restrictions, including trade and export controls. U.S. government actions restricting our ability to sell products in or source components from certain countries could adversely affect our business. China accounted for approximately 19% of net revenue ($74.2 billion) in fiscal 2022. Manufacturing is heavily concentrated in China, including substantially all iPhone assembly. Geopolitical tensions between the U.S. and China, including around Taiwan, could disrupt our supply chain and market access.' Apple's market cap was approximately $2.3 trillion.""",
        "question": "Did the China geopolitical risk materially impact Apple's revenue or operations within 18 months?",
        "correct_answer": "no",
        "explanation": "Despite the COVID lockdown-related iPhone production disruptions in Q4 2022 (Zhengzhou factory protests), Apple's China revenue remained resilient and the company successfully began diversifying manufacturing to India and Vietnam. No material U.S.-China trade restrictions were imposed on Apple products during this period.",
        "domain": "finance",
    },
    {
        "id": "rf_016",
        "scenario_type": "risk_factor",
        "difficulty": 4,
        "scenario": """United Kingdom Gilt Market / UK Pension Funds (2021 disclosures): 'Liability-driven investment (LDI) strategies use leverage and interest rate derivatives to match pension liabilities. These strategies include interest rate swaps and leveraged gilt positions, typically with 3-4x leverage. A rapid increase in long-dated gilt yields would trigger margin calls requiring liquid collateral. The pension schemes hold approximately £1.5 trillion in LDI strategies. Simultaneous margin calls across the sector could create forced selling dynamics, as funds may need to liquidate gilt holdings to meet collateral demands, potentially creating a reflexive cycle of rising yields and further margin calls.' Most pension fund trustees and corporate risk committees considered rapid yield spikes to be a tail risk given the Bank of England's forward guidance.""",
        "question": "Did the margin call and forced selling risk in LDI strategies materially impact UK pension funds within 18 months?",
        "correct_answer": "yes",
        "explanation": "In September 2022, the Truss government's mini-budget triggered a gilt market crisis. Long-dated gilt yields spiked ~150bps in days, causing cascading LDI margin calls and forced gilt sales that threatened pension fund solvency, forcing the Bank of England into emergency gilt purchases to prevent systemic collapse.",
        "domain": "finance",
    },
    {
        "id": "rf_017",
        "scenario_type": "risk_factor",
        "difficulty": 4,
        "scenario": """Microsoft Corporation (MSFT) 10-K FY2022 (filed July 2022): 'We face significant competition in cloud computing from Amazon Web Services, Google Cloud, and others. Competitive pricing pressure could reduce margins in our Intelligent Cloud segment. Additionally, regulatory scrutiny of large technology companies globally, including antitrust investigations in the EU, UK, and U.S., could result in restrictions on our business practices, acquisitions, or bundling of products. Our proposed acquisition of Activision Blizzard for $68.7 billion is subject to regulatory approval and may not be completed.' Azure revenue had grown 46% year-over-year in FY2022, and total Intelligent Cloud revenue was $75 billion.""",
        "question": "Did antitrust regulatory risk materially block or impair the Activision Blizzard acquisition within 18 months?",
        "correct_answer": "no",
        "explanation": "Despite significant FTC opposition (including an injunction attempt that failed in court) and a lengthy UK CMA review that initially blocked the deal, Microsoft ultimately closed the $68.7 billion Activision Blizzard acquisition in October 2023 with restructured cloud gaming rights — the deal completed within the 18-month window.",
        "domain": "finance",
    },

    # ── D5 (Near-Impossible / Surprising) ─────────────────────────────────
    {
        "id": "rf_018",
        "scenario_type": "risk_factor",
        "difficulty": 5,
        "scenario": """Adani Group (Adani Enterprises, Adani Green, Adani Ports — FY2022 annual reports): 'Certain Adani Group entities have complex ownership structures involving promoter-held shares pledged as collateral and entities domiciled in Mauritius and other offshore jurisdictions. Concentrated promoter ownership (~73% across listed entities) means any forced sale of pledged shares could significantly impact market prices. The Group's aggressive expansion — acquiring ports, airports, cement, media, and green energy assets — is partially funded through leverage. Consolidated Group debt across listed entities exceeded $30 billion.' The Group's combined market capitalization had grown from ~$40 billion to ~$260 billion in two years, making Gautam Adani briefly the world's second-richest person.""",
        "question": "Did the pledged share and offshore entity structure risk materially impact Adani Group market value within 18 months?",
        "correct_answer": "yes",
        "explanation": "In January 2023, Hindenburg Research published a short-seller report alleging stock manipulation, accounting fraud, and undisclosed related-party transactions through offshore shells. Adani Group lost over $150 billion in market value in two weeks, Adani Enterprises' $2.5B FPO was pulled, and multiple entities faced credit rating downgrades.",
        "domain": "finance",
    },
    {
        "id": "rf_019",
        "scenario_type": "risk_factor",
        "difficulty": 5,
        "scenario": """Saudi Aramco (2021 Annual Report): 'Our business is subject to risks associated with the global energy transition. Increasing adoption of electric vehicles, renewable energy, and government net-zero commitments could reduce long-term demand for petroleum products. We are investing in hydrogen, carbon capture, and renewables to diversify. Our revenue is heavily dependent on crude oil prices — a $1/bbl change in realized price impacts annual revenue by approximately $3.3 billion. Geopolitical risks in the Middle East, including potential attacks on production infrastructure, could temporarily disrupt operations.' Aramco reported record net income of $110 billion in 2021 on the back of recovering oil prices. Analysts broadly expected demand destruction from EVs to begin pressuring oil majors by 2023-2024.""",
        "question": "Did the energy transition and EV adoption risk materially impact Saudi Aramco's revenue or valuation within 18 months?",
        "correct_answer": "no",
        "explanation": "Far from declining, Aramco posted record-breaking $161 billion in net income for FY2022, driven by the Russia-Ukraine energy crisis pushing oil prices above $100/bbl. EV adoption, while accelerating, did not dent global oil demand which hit record highs in 2023. The energy transition risk remained firmly long-term.",
        "domain": "finance",
    },
    {
        "id": "rf_020",
        "scenario_type": "risk_factor",
        "difficulty": 5,
        "scenario": """First Republic Bank (FRC) 10-K FY2022 (filed February 2023): 'We serve high-net-worth individuals and businesses with an emphasis on personalized service. Our deposit base includes a significant proportion of uninsured deposits. As of December 31, 2022, approximately 68% of our deposits exceeded FDIC insurance limits. Our single-family residential mortgage portfolio of $102 billion has a weighted average LTV of 59% and average FICO of 775, representing high credit quality. We have historically experienced minimal credit losses. Our business model generates net interest margin through holding high-quality, low-yielding long-duration mortgage assets funded by deposits.' First Republic was considered a conservatively managed bank serving affluent clients, with a pristine credit quality record. Most analysts viewed it as well-positioned compared to peers.""",
        "question": "Did the uninsured deposit concentration risk materially impact First Republic Bank within 18 months?",
        "correct_answer": "yes",
        "explanation": "Following the SVB collapse in March 2023, First Republic experienced $100+ billion in deposit outflows within days despite having minimal credit risk. The bank was seized by the FDIC and sold to JPMorgan Chase in May 2023 — demonstrating that pristine credit quality could not offset deposit concentration risk in a contagion environment.",
        "domain": "finance",
    },
]

# %%
# === Scoring Functions ===

def compute_ece(confidences, accuracies, n_bins=10):
    """Expected Calibration Error."""
    confs = np.array(confidences)
    accs = np.array(accuracies, dtype=float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (confs > bins[i]) & (confs <= bins[i+1])
        if np.any(mask):
            ece += np.sum(mask) / len(confs) * abs(np.mean(accs[mask]) - np.mean(confs[mask]))
    return round(float(ece), 4)

def compute_brier(confidences, accuracies):
    """Brier Score."""
    return round(float(np.mean((np.array(confidences) - np.array(accuracies, dtype=float))**2)), 4)

def compute_wwa(accuracies, wagers, penalty_mult=2.0):
    """Wager-Weighted Accuracy (novel metric)."""
    accs = np.array(accuracies, dtype=float)
    wags = np.array(wagers, dtype=float) / 100.0
    gains = wags * accs
    losses = penalty_mult * wags * (1 - accs)
    raw = float(np.sum(gains - losses))
    max_possible = float(np.sum(wags))
    return round(raw / max_possible if max_possible > 0 else 0.0, 4)

# %%
# === Sub-task: Single Vulnerability Assessment ===

@kbench.task(store_task=False)
def eval_vuln(llm, scenario: str, item_id: str) -> dict:
    prompt = f"""You are a cybersecurity expert assessing vulnerabilities and threats.

## Scenario
{scenario}

## Task
1. Provide your assessment/classification as requested
2. State confidence (0.0 to 1.0)
3. Wager 0-100 points. Correct = +wager. Incorrect = -2x wager.

Respond in JSON: {{"severity_or_answer": "your answer", "explanation": "brief explanation", "confidence": 0.0-1.0, "wager": 0-100, "reasoning": "why this wager amount"}}"""

    resp = llm.prompt(prompt, schema=VulnResponse)
    return {"id": item_id, "response": resp}

# %%
# === Sub-task: Single Risk Factor evaluation ===

@kbench.task(store_task=False)
def eval_risk_factor(llm, company: str, sector: str, year: int, risk: str, item_id: str) -> dict:
    prompt = f"""You are a financial analyst assessing risk factor materiality.

## Company: {company} — {sector} (Fiscal Year {year})

## Risk Factor (from 10-K):
"{risk}"

## Task
Did this risk MATERIALIZE in the 12 months following disclosure?
1. Answer: materialized / did_not_materialize
2. Confidence (0.0-1.0)
3. Wager (0-100). Correct = +wager. Wrong = -2x wager.

Respond in JSON: {{"assessment": "materialized|did_not_materialize", "rationale": "...", "confidence": 0.0-1.0, "wager": 0-100, "reasoning": "..."}}"""

    resp = llm.prompt(prompt, schema=RiskFactorResponse)
    return {"id": item_id, "response": resp}

# %%
# === Main Benchmark Task ===

@kbench.task(name="mc1_calibrated_confidence")
def calibrated_confidence_benchmark(llm) -> float:
    """
    MC-1: Calibrated Confidence Under Stakes

    Measures metacognitive monitoring accuracy using a wagering paradigm.
    Tests calibration, discrimination, and behavioral confidence across
    cybersecurity (vulnerability assessment) and finance (risk factor materiality).

    Returns: Composite metacognition score (0-1, higher = better).
    """

    all_confidences = []
    all_accuracies = []
    all_wagers = []
    cyber_scores = {"confidences": [], "accuracies": [], "wagers": []}
    fin_scores = {"confidences": [], "accuracies": [], "wagers": []}

    # Cybersecurity: Vulnerability assessments
    print("\n--- Cybersecurity Domain: Vulnerability Assessment ---")
    for item in CYBER_ITEMS:
        result = eval_vuln.run(
            llm=llm,
            scenario=item["prompt"],
            item_id=item["id"],
        )
        resp = result["response"]
        answer = resp.severity_or_answer.lower().strip().replace(" ", "_")
        is_correct = answer == item["correct"] or item["correct"] in answer
        conf = max(0.0, min(1.0, resp.confidence))
        wager = max(0, min(100, resp.wager))

        cyber_scores["confidences"].append(conf)
        cyber_scores["accuracies"].append(is_correct)
        cyber_scores["wagers"].append(wager)
        all_confidences.append(conf)
        all_accuracies.append(is_correct)
        all_wagers.append(wager)

        status = "CORRECT" if is_correct else "WRONG"
        print(f"  [{item['id']}] D{item['difficulty']} {item['type']}: "
              f"{answer} ({status}) conf={conf:.2f} wager={wager}")

    # Finance: Risk factors
    print("\n--- Finance Domain: Risk Factor Materiality ---")
    for item in RF_ITEMS:
        result = eval_risk_factor.run(
            llm=llm,
            company=item["company"], sector=item["sector"],
            year=item["year"], risk=item["risk"],
            item_id=item["id"],
        )
        resp = result["response"]
        expected = "materialized" if item["materialized"] else "did_not_materialize"
        is_correct = resp.assessment.lower().strip().replace(" ", "_") == expected
        conf = max(0.0, min(1.0, resp.confidence))
        wager = max(0, min(100, resp.wager))

        fin_scores["confidences"].append(conf)
        fin_scores["accuracies"].append(is_correct)
        fin_scores["wagers"].append(wager)
        all_confidences.append(conf)
        all_accuracies.append(is_correct)
        all_wagers.append(wager)

        status = "CORRECT" if is_correct else "WRONG"
        print(f"  [{item['id']}] D{item['difficulty']} {item['company']}: "
              f"{resp.assessment} ({status}) conf={conf:.2f} wager={wager}")

    # Compute metrics
    overall_ece = compute_ece(all_confidences, all_accuracies)
    overall_brier = compute_brier(all_confidences, all_accuracies)
    overall_wwa = compute_wwa(all_accuracies, all_wagers)
    overall_accuracy = round(sum(all_accuracies) / len(all_accuracies), 4)

    cyber_ece = compute_ece(cyber_scores["confidences"], cyber_scores["accuracies"])
    fin_ece = compute_ece(fin_scores["confidences"], fin_scores["accuracies"])

    # Assertions
    kbench.assertions.assert_true(
        overall_ece < 0.4,
        expectation="ECE should be below 0.4 (reasonable calibration)"
    )
    kbench.assertions.assert_true(
        overall_wwa > -0.5,
        expectation="Wager-weighted accuracy should be above -0.5 (not catastrophically overconfident)"
    )

    print(f"\n{'='*50}")
    print(f"MC-1 CALIBRATED CONFIDENCE RESULTS")
    print(f"{'='*50}")
    print(f"Overall Accuracy:          {overall_accuracy:.2%}")
    print(f"Overall ECE:               {overall_ece:.4f} (lower = better)")
    print(f"Overall Brier Score:       {overall_brier:.4f} (lower = better)")
    print(f"Wager-Weighted Accuracy:   {overall_wwa:.4f} (higher = better)")
    print(f"Cybersecurity ECE:         {cyber_ece:.4f}")
    print(f"Finance ECE:               {fin_ece:.4f}")
    print(f"Cross-Domain ECE Gap:      {abs(cyber_ece - fin_ece):.4f}")
    print(f"{'='*50}")

    # Composite score: 1 - ECE (so higher = better, matching Kaggle leaderboard convention)
    composite = 1.0 - overall_ece
    return float(composite)


# %%
calibrated_confidence_benchmark.run(llm=kbench.llm)

# %%
%choose mc1_calibrated_confidence
