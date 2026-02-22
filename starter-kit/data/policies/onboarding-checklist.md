---
title: New Employee IT Onboarding Checklist
tags: [onboarding, new-hire, setup, checklist]
---

# New Employee IT Onboarding Checklist

**Last Updated:** February 10, 2026
**Maintained By:** IT Operations & People Ops
**Contact:** onboarding@acmecorp.com or Slack #it-onboarding

---

## Overview

Welcome to Acme Corp! This checklist covers everything you need to get set up with our IT systems and tools. Your IT onboarding buddy and manager will guide you through the process, but this document serves as your comprehensive reference.

Checkboxes below are for tracking purposes. Work through them with your onboarding buddy during your first week.

---

## Pre-Start (Handled by IT Before Day 1)

The IT team will complete these items before your start date:

- [ ] Laptop ordered and configured (MacBook Pro or Dell Latitude based on role)
- [ ] Okta account created (your-name@acmecorp.com)
- [ ] Google Workspace account provisioned
- [ ] Slack workspace invitation sent
- [ ] Building badge and access card prepared
- [ ] Desk assignment confirmed with Facilities
- [ ] Welcome email sent with Day 1 instructions

---

## Day 1: First Day Setup

### Morning (9:00 AM - 12:00 PM)

- [ ] **Pick up equipment** from IT desk (HQ Floor 3, Room 305):
  - Laptop with charger
  - External monitor (if requested)
  - Keyboard and mouse
  - Headset
  - Docking station (if applicable)
  - Building badge and access card

- [ ] **Laptop initial setup:**
  - Power on and sign in with your temporary credentials (provided in welcome email)
  - Set a new password meeting the [security policy requirements](policy://security-policy) (14+ characters, 3 of 4 character types)
  - Enable FileVault disk encryption (IT will verify via Jamf)
  - Connect to Wi-Fi: `AcmeCorp-Secure` (authenticate with Okta)

- [ ] **Okta SSO activation:**
  - Navigate to https://acmecorp.okta.com
  - Log in with your @acmecorp.com email and temporary password
  - Complete MFA setup:
    - Primary: Install Okta Verify on your phone
    - Backup: Register a hardware security key (YubiKey provided by IT if applicable)

- [ ] **Google Workspace setup:**
  - Access Gmail at https://mail.google.com
  - Set up email signature (template at https://intranet.acmecorp.com/brand/email-signature)
  - Configure Google Calendar with your working hours and time zone
  - Join team shared drives as directed by your manager

### Afternoon (1:00 PM - 5:00 PM)

- [ ] **Slack setup:**
  - Download Slack desktop app (https://slack.com/downloads)
  - Sign in via Okta SSO
  - Complete your profile:
    - Full name, role, department
    - Profile photo
    - Phone number
    - Manager name
    - Start date
  - Join mandatory channels:
    - #general
    - #company-announcements
    - #it-helpdesk
    - #security-incidents
    - Your department channel (your manager will share)
    - Your team channel

- [ ] **Building badge activation:**
  - Visit the Security desk on Floor 1 for badge photo
  - Test badge access on your assigned floor
  - Verify access to common areas (kitchen, gym, parking garage if applicable)

- [ ] **1Password setup:**
  - Accept the 1Password invitation email
  - Install the 1Password desktop app and browser extension
  - Create your Master Password (unique, not used anywhere else)
  - Enable biometric unlock

---

## Day 2-3: Tool Access & Configuration

### Core Tools Setup

Work through these with your onboarding buddy:

- [ ] **Jira access:**
  - Log in at https://acmecorp.atlassian.net via Okta
  - Request access to your team's Jira project (your manager will approve)
  - Familiarize yourself with the team board and workflow

- [ ] **Confluence access:**
  - Log in via Okta
  - Bookmark your team's Confluence space
  - Read the team's "Getting Started" page (your manager will share the link)
  - Review the company-wide Confluence spaces:
    - Engineering Handbook
    - HR Policies
    - IT Knowledge Base

- [ ] **GitHub access:**
  - Accept the GitHub organization invitation (sent to your @acmecorp.com email)
  - Set up SSH keys:
    ```
    ssh-keygen -t ed25519 -C "your-name@acmecorp.com"
    ```
  - Add the public key to your GitHub profile
  - Enable 2FA on GitHub (hardware key preferred)
  - Clone the team repository as directed by your manager
  - Review the contribution guidelines in CONTRIBUTING.md

- [ ] **Figma access** (design & product roles):
  - Accept the Figma team invitation
  - Install the Figma desktop app
  - Review the Acme Corp Design System library

- [ ] **VPN setup:**
  - Follow the [VPN Setup & Usage Guide](policy://vpn-guide)
  - Download your WireGuard configuration from the IT Self-Service Portal
  - Test VPN connection from the office (to verify it works before going remote)
  - Bookmark internal sites:
    - https://intranet.acmecorp.com
    - https://itportal.acmecorp.com
    - https://status.acmecorp.com

### Communication Tools

- [ ] **Zoom account:**
  - Log in at https://zoom.us via Okta SSO
  - Install the Zoom desktop client
  - Test audio and video
  - Set up your Personal Meeting ID and waiting room

- [ ] **Google Meet:**
  - No separate setup needed (part of Google Workspace)
  - Test a call with your onboarding buddy

---

## Day 4-5: Security Training & Compliance

- [ ] **Security awareness training:**
  - Complete the "New Hire Security Fundamentals" course in KnowBe4
  - Duration: approximately 45 minutes
  - Topics covered:
    - Phishing identification
    - Password security
    - Data classification
    - Clean desk policy
    - Incident reporting
  - **Deadline:** Must be completed by end of Week 1

- [ ] **Policy acknowledgments** (complete in Workday):
  - [ ] Information Security Policy
  - [ ] Remote Work Policy
  - [ ] Acceptable Use Policy
  - [ ] Expense Reimbursement Policy
  - [ ] Code of Conduct
  - [ ] Data Privacy Policy

- [ ] **Phishing test baseline:**
  - You will receive a simulated phishing email during your first week
  - This establishes your baseline (no penalty for clicking)
  - Review the "How to Report Phishing" guide after the test

---

## Week 1: Equipment Requests

If you need additional equipment beyond your standard setup, submit requests through the IT Self-Service Portal:

- [ ] **Review your equipment needs:**
  - Second monitor
  - Ergonomic keyboard (Microsoft Ergonomic Keyboard, Kinesis Advantage360)
  - Trackpad (Apple Magic Trackpad)
  - Laptop stand (Rain Design mStand)
  - USB-C hub or dock
  - Webcam upgrade
  - Additional cables

- [ ] **Submit equipment request:**
  - Go to https://itportal.acmecorp.com/equipment
  - Select items from the catalog
  - Your manager will approve the request
  - IT will fulfill within 3-5 business days

- [ ] **Home office stipend** (if eligible for remote work):
  - After 90 days, you become eligible for the $1,500 home office stipend
  - See the [Remote Work Policy](policy://remote-work) for details

---

## Week 2: Team Integration

- [ ] **Meet your IT onboarding buddy** for a wrap-up session:
  - Review any outstanding setup items
  - Q&A on tools and processes
  - Confirm all systems are working

- [ ] **Access verification:**
  - [ ] Can send and receive email
  - [ ] Can access Slack and all required channels
  - [ ] Can access Jira and see team board
  - [ ] Can access Confluence and team space
  - [ ] Can access GitHub and clone repositories
  - [ ] VPN connects successfully from outside the office
  - [ ] Can print to your floor's printer
  - [ ] Building badge works on all required doors

- [ ] **Manager 1:1:**
  - Review 30/60/90 day milestones
  - Confirm tool access is complete
  - Discuss team communication norms and meeting schedules

---

## 30/60/90 Day IT Milestones

### Day 30

- [ ] All tools and systems set up and actively used
- [ ] Security training completed and acknowledged
- [ ] VPN tested from home/remote location
- [ ] Equipment requests fulfilled
- [ ] Comfortable with Jira/Confluence workflows
- [ ] 1Password vault organized with all work credentials

### Day 60

- [ ] Remote work eligible (if applicable, after 90-day probation, but begin prep)
- [ ] Familiar with IT self-service tools and knowledge base
- [ ] Completed first quarterly security awareness module
- [ ] Submitted first expense report in Concur (if applicable)

### Day 90

- [ ] Remote work application submitted (if desired)
- [ ] All policy acknowledgments up to date
- [ ] Fully autonomous with IT tools and processes
- [ ] Know how to submit IT tickets and equipment requests
- [ ] Onboarding feedback submitted to People Ops

---

## IT Mentor / Onboarding Buddy

Your IT onboarding buddy is assigned by the IT team and will be your go-to person for the first 30 days for any setup questions or technical issues.

**Your buddy will help with:**
- Laptop and tool setup
- Navigating the IT Self-Service Portal
- Understanding team-specific tool configurations
- Connecting you with the right IT resources

**Your buddy is NOT:**
- A replacement for the IT Help Desk (for issues, use Slack #it-helpdesk)
- Your only resource (feel free to ask anyone on the team)

---

## Frequently Asked Questions

**Q: What if my laptop has a hardware issue on Day 1?**
A: Visit IT on Floor 3, Room 305. We keep spare laptops configured and ready for immediate swap.

**Q: Can I install personal software on my work laptop?**
A: Limited personal use is allowed per the Acceptable Use Policy. Software installations must be approved through the IT Self-Service Portal. Contact IT if you need specific development tools.

**Q: What if I forget my Okta password?**
A: Use the self-service password reset at https://acmecorp.okta.com/forgot-password. If locked out, contact IT Help Desk.

**Q: When do I get VPN access?**
A: VPN access is provisioned on Day 1 as part of your Okta account setup. Follow the VPN Guide to configure your client.

**Q: I need software not in the standard list. How do I request it?**
A: Submit a Software Request through the IT Self-Service Portal. IT Security will review and approve within 3 business days.

---

## Contact & Support

- **IT Help Desk:** Slack #it-helpdesk or it-support@acmecorp.com
- **IT Onboarding:** onboarding@acmecorp.com
- **IT Self-Service Portal:** https://itportal.acmecorp.com
- **Security Questions:** security@acmecorp.com
- **HR / People Ops:** people@acmecorp.com
- **Facilities:** facilities@acmecorp.com

---

*This checklist is maintained by IT Operations. Last reviewed: February 2026. Report errors or suggestions to it-ops@acmecorp.com.*
