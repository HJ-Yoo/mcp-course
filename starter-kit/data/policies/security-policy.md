---
title: Information Security Policy
tags: [security, password, mfa, data, compliance]
---

# Information Security Policy

**Effective Date:** January 1, 2026
**Last Revised:** February 1, 2026
**Policy Owner:** Chief Information Security Officer (CISO), IT Security Team
**Applies To:** All employees, contractors, vendors, and third parties with access to Acme Corp systems

---

## 1. Purpose

This policy defines the security requirements and controls that protect Acme Corp's information assets, systems, and data. All personnel with access to company systems are responsible for understanding and complying with this policy. Violations may result in disciplinary action, up to and including termination and legal proceedings.

---

## 2. Password Requirements

2.1. **Minimum Length:** All passwords must be at least **14 characters** long.

2.2. **Complexity Rules:** Passwords must contain at least three of the following four character types:
   - Uppercase letters (A-Z)
   - Lowercase letters (a-z)
   - Numbers (0-9)
   - Special characters (!@#$%^&*()-_=+[]{}|;:',.<>?/)

2.3. **Password Rotation:** Passwords must be changed every **90 days**. The system will prompt you 14 days before expiration. Passwords cannot be reused within the last 12 password cycles.

2.4. **Prohibited Passwords:** The following are not permitted:
   - Dictionary words or common phrases
   - Personal information (name, birthday, employee ID)
   - Sequential or repeated characters (e.g., "aaaaaa", "123456")
   - Passwords found in known breach databases (checked automatically)

2.5. **Password Manager:** All employees are required to use **1Password** (company-provided) to generate and store passwords. Storing passwords in browsers, sticky notes, text files, or spreadsheets is strictly prohibited.

2.6. **Shared Accounts:** Shared or generic accounts are prohibited. Every individual must use their own uniquely identified account for all system access.

---

## 3. Multi-Factor Authentication (MFA)

3.1. **Mandatory MFA:** Multi-factor authentication is required for all Acme Corp systems, including:
   - Okta SSO (primary identity provider)
   - Email (Google Workspace)
   - VPN access
   - GitHub
   - AWS Console and CLI
   - Jira, Confluence, and other Atlassian products
   - Slack (when accessing from a new device)
   - Any system containing Confidential or Restricted data

3.2. **Preferred Method:** **Hardware security keys** (YubiKey 5 series) are the preferred MFA method and are required for all employees with access to production systems or Restricted data. IT will provide up to 2 YubiKeys per employee (primary and backup).

3.3. **Acceptable Methods:** In order of preference:
   1. Hardware security key (YubiKey) — **required for engineering, IT, finance**
   2. Okta Verify push notification
   3. TOTP authenticator app (1Password, Google Authenticator)
   4. SMS-based OTP — **not permitted** (vulnerable to SIM swapping)

3.4. **Recovery:** If an employee loses their hardware key, they must report it to IT Security immediately via Slack #security-incidents or email security@acmecorp.com. A temporary bypass will be issued (valid 24 hours) while a replacement key is provisioned.

---

## 4. Device Security

4.1. **Full Disk Encryption:** All devices used to access Acme Corp systems must have full disk encryption enabled:
   - **macOS:** FileVault must be enabled and verified via Jamf
   - **Windows:** BitLocker must be enabled with TPM
   - **Linux:** LUKS full disk encryption required

4.2. **Automatic Screen Lock:** Devices must lock automatically after **5 minutes** of inactivity. Manual locking (Cmd+Ctrl+Q on macOS, Win+L on Windows) should be used whenever stepping away.

4.3. **Operating System Updates:** Security patches must be applied within **72 hours** of release for critical vulnerabilities and within **14 days** for all other updates. IT manages patch deployment through Jamf (macOS) and Intune (Windows).

4.4. **Antivirus & Endpoint Protection:** All company devices must run the approved endpoint protection software:
   - **CrowdStrike Falcon** is deployed on all managed devices
   - Tamper protection must remain enabled
   - Real-time scanning must be active at all times

4.5. **Mobile Devices:** Personal mobile devices accessing company email or Slack must have:
   - Screen lock with biometric or 6+ digit PIN
   - Latest OS version (within one major version)
   - Remote wipe capability via Okta MDM enrollment

---

## 5. Data Classification

5.1. All data at Acme Corp is classified into four levels:

| Classification | Description | Examples | Handling |
|---|---|---|---|
| **Public** | Information intended for public consumption | Marketing materials, blog posts, press releases | No restrictions |
| **Internal** | General business information not intended for external sharing | Meeting notes, internal announcements, org charts | Do not share externally; no special encryption required |
| **Confidential** | Sensitive business information whose disclosure could harm the company | Financial reports, product roadmaps, customer lists, source code | Encrypted storage and transmission; need-to-know access; NDA required for external sharing |
| **Restricted** | Highly sensitive data subject to regulatory or legal requirements | PII, PHI, payment card data, trade secrets, security credentials | Encrypted at rest and in transit; strict access controls; audit logging; DLP monitoring |

5.2. **Default Classification:** All data is classified as **Internal** unless explicitly marked otherwise. Employees should err on the side of higher classification when uncertain.

5.3. **Labeling:** Documents containing Confidential or Restricted data must be labeled in the header or footer. Digital files should include the classification in the filename or metadata.

---

## 6. Clean Desk Policy

6.1. **End of Day:** At the end of each workday (or when leaving for an extended period), employees must:
   - Lock their computer screen
   - Store all printed documents containing Internal, Confidential, or Restricted information in a locked drawer or cabinet
   - Remove all sticky notes containing passwords, PINs, or access codes (these should not exist per Section 2.5)
   - Clear whiteboards of any sensitive information

6.2. **Shared Spaces:** Meeting rooms and shared workspaces must be cleared of all documents and notes at the conclusion of each meeting. Use the shred bins located on each floor for sensitive paper disposal.

6.3. **Printing:** Use "secure print" (pull printing) for all documents containing Confidential or Restricted data. Documents left uncollected at the printer for more than 1 hour will be automatically shredded by facilities staff.

---

## 7. Incident Reporting

7.1. **Reporting Timeline:** All security incidents must be reported **within 1 hour** of discovery. Failure to report a known security incident is itself a policy violation.

7.2. **What to Report:**
   - Suspected phishing emails or social engineering attempts
   - Lost or stolen devices (laptops, phones, security keys)
   - Unauthorized access to systems or data
   - Malware or suspicious software behavior
   - Accidental data exposure or misdirected emails
   - Physical security breaches (tailgating, unauthorized visitors)

7.3. **How to Report:**
   - **Immediate:** Slack #security-incidents (24/7 monitored by Security Operations)
   - **Email:** security@acmecorp.com
   - **Phone:** +1 (555) 012-3456 (Security Operations Center)
   - **Phishing:** Forward suspicious emails to phishing@acmecorp.com using the "Report Phishing" button in Gmail

7.4. **No Retaliation:** Acme Corp has a strict no-retaliation policy for good-faith security incident reports. Employees will never be penalized for reporting potential incidents, even if the report turns out to be a false alarm.

---

## 8. Acceptable Use

8.1. **Business Use:** Company devices, networks, and systems are provided primarily for business use. Limited personal use is permitted provided it does not:
   - Interfere with job responsibilities
   - Violate any law or regulation
   - Compromise system security
   - Consume excessive network bandwidth

8.2. **Prohibited Activities:**
   - Installing unauthorized software or browser extensions
   - Disabling security controls (antivirus, firewall, encryption)
   - Sharing credentials with any other person, including IT staff
   - Accessing or storing illegal content
   - Using company resources for cryptocurrency mining
   - Connecting unauthorized devices to the corporate network
   - Using personal cloud storage (Dropbox, personal Google Drive) for company data

8.3. **Monitoring:** Acme Corp reserves the right to monitor all activity on company-owned devices and networks. This includes email, web browsing, file access, and application usage. Monitoring is conducted in compliance with applicable laws.

---

## 9. BYOD (Bring Your Own Device)

9.1. **Permitted Use:** Personal devices may be used to access company email and Slack only after enrollment in Okta MDM and completion of the BYOD agreement form.

9.2. **Requirements for BYOD:**
   - Device must meet minimum OS version requirements
   - Screen lock must be enabled (biometric or 6+ digit PIN)
   - Device encryption must be enabled
   - Remote wipe consent must be signed
   - Company data must be stored in managed apps only (no copying to personal apps)

9.3. **Separation of Data:** BYOD devices use containerized access through Okta. Company data is isolated in a managed container that can be selectively wiped without affecting personal data.

9.4. **Lost/Stolen BYOD:** Personal devices with company access that are lost or stolen must be reported within 1 hour. IT will initiate a selective wipe of the managed container.

---

## 10. Phishing & Security Awareness Training

10.1. **Quarterly Training:** All employees must complete security awareness training every quarter. Training is delivered through KnowBe4 and covers:
   - Phishing identification and reporting
   - Social engineering tactics
   - Password hygiene
   - Data handling procedures
   - Physical security

10.2. **Phishing Simulations:** IT Security conducts monthly phishing simulations. Employees who click on simulated phishing links will be enrolled in additional targeted training.

10.3. **Completion Deadline:** Training must be completed within 14 days of assignment. Non-completion will result in a reminder from HR, followed by restricted system access after 30 days.

---

## 11. Vendor & Third-Party Access

11.1. **Access Requests:** All vendor and third-party access must be requested through the IT Service Portal and approved by both the requesting manager and IT Security.

11.2. **Principle of Least Privilege:** Vendors receive the minimum access necessary to perform their contracted work. Access is time-limited and expires automatically.

11.3. **NDA Requirement:** All vendors must sign a Non-Disclosure Agreement before receiving access to any Internal, Confidential, or Restricted data.

11.4. **Audit:** Vendor access is reviewed monthly by IT Security. Access for completed engagements is revoked within 24 hours of contract end.

---

## 12. Network Security

12.1. **VPN Required:** All remote access to internal systems must go through the Acme Corp VPN. See the VPN Setup & Usage Guide (policy://vpn-guide) for details.

12.2. **Network Segmentation:** The corporate network is segmented into zones:
   - **Corporate:** General employee access
   - **Engineering:** Development and staging environments
   - **Production:** Production infrastructure (restricted access)
   - **Guest:** Isolated guest Wi-Fi (no internal access)

12.3. **Wireless Security:** Corporate Wi-Fi uses WPA3-Enterprise with certificate-based authentication through Okta. The guest network uses a rotating password changed weekly.

---

## 13. Compliance & Enforcement

13.1. **Compliance Monitoring:** IT Security conducts regular compliance audits using automated tools and manual reviews. Non-compliant devices may have network access restricted until remediation is complete.

13.2. **Violations:** Violations of this policy are taken seriously and may result in:
   - First offense: Written warning and mandatory remedial training
   - Second offense: Temporary suspension of system access and formal HR action
   - Severe violations: Immediate termination and potential legal action

13.3. **Annual Review:** This policy is reviewed annually by the CISO and updated as needed to reflect evolving threats and regulatory requirements.

---

## 14. Contact

- **IT Security Team:** security@acmecorp.com
- **Security Incidents (24/7):** Slack #security-incidents or +1 (555) 012-3456
- **Phishing Reports:** phishing@acmecorp.com
- **IT Help Desk:** it-support@acmecorp.com or Slack #it-helpdesk

---

*All employees must acknowledge this policy annually through the compliance portal in Workday. Last acknowledgment cycle completed: January 2026.*
