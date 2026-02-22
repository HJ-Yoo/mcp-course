---
title: VPN Setup & Usage Guide
tags: [vpn, network, remote, security, setup]
---

# VPN Setup & Usage Guide

**Last Updated:** February 5, 2026
**Maintained By:** IT Infrastructure Team
**Support:** Slack #vpn-support or it-support@acmecorp.com

---

## 1. Overview

All Acme Corp employees must connect to the corporate VPN before accessing internal systems from outside the office network. The VPN encrypts your traffic and provides secure access to internal resources such as Jira, Confluence, internal dashboards, staging environments, and the corporate intranet.

---

## 2. Supported VPN Clients

| Priority | Client | Platforms | Notes |
|---|---|---|---|
| **Preferred** | WireGuard | macOS, Windows, Linux, iOS, Android | Fastest performance, lowest battery impact |
| **Fallback** | OpenVPN (via Tunnelblick/OpenVPN Connect) | macOS, Windows, Linux, iOS, Android | Use if WireGuard is blocked by your ISP/network |

**Important:** Only use the Acme Corp-provided configuration files. Do not use third-party VPN services to access corporate resources.

---

## 3. Setup Instructions

### 3.1. macOS (WireGuard - Preferred)

1. Install WireGuard from the Mac App Store or via Homebrew:
   ```
   brew install wireguard-tools
   ```
2. Download your personal configuration file from the IT Self-Service Portal (https://itportal.acmecorp.com/vpn).
   - Log in with your Okta credentials
   - Navigate to **VPN > Download Config > WireGuard**
   - The file will be named `acme-wg-{your-username}.conf`
3. Open WireGuard and click **Import Tunnel(s) from File**.
4. Select the downloaded `.conf` file.
5. Toggle the tunnel **ON** to connect.
6. Verify connectivity by visiting https://intranet.acmecorp.com. You should see the Acme Corp intranet homepage.

### 3.2. macOS (OpenVPN - Fallback)

1. Install Tunnelblick from https://tunnelblick.net or via Homebrew:
   ```
   brew install --cask tunnelblick
   ```
2. Download your OpenVPN configuration from the IT Self-Service Portal.
   - Navigate to **VPN > Download Config > OpenVPN**
   - The file will be named `acme-ovpn-{your-username}.ovpn`
3. Double-click the `.ovpn` file to import it into Tunnelblick.
4. Click the Tunnelblick icon in the menu bar and select **Connect acme-ovpn**.
5. Enter your Okta credentials when prompted. Approve the MFA push notification.

### 3.3. Windows

1. Download WireGuard from https://www.wireguard.com/install/.
2. Download your configuration file from the IT Self-Service Portal.
3. Open WireGuard, click **Add Tunnel** and select the `.conf` file.
4. Click **Activate** to connect.
5. Verify by navigating to https://intranet.acmecorp.com.

For OpenVPN fallback:
1. Download OpenVPN Connect from https://openvpn.net/client/.
2. Import the `.ovpn` file and connect with Okta credentials + MFA.

### 3.4. Linux

1. Install WireGuard:
   ```
   # Ubuntu/Debian
   sudo apt install wireguard

   # Fedora
   sudo dnf install wireguard-tools

   # Arch
   sudo pacman -S wireguard-tools
   ```
2. Copy the configuration file to `/etc/wireguard/acme-wg0.conf`.
3. Start the tunnel:
   ```
   sudo wg-quick up acme-wg0
   ```
4. To auto-start on boot:
   ```
   sudo systemctl enable wg-quick@acme-wg0
   ```
5. Verify with `curl -s https://intranet.acmecorp.com | head -5`.

### 3.5. iOS

1. Install WireGuard from the App Store.
2. On your iPhone/iPad, visit the IT Self-Service Portal in Safari.
3. Download the WireGuard configuration. iOS will prompt to open it in the WireGuard app.
4. Approve the VPN configuration installation.
5. Toggle the tunnel on from the WireGuard app or Settings > VPN.

### 3.6. Android

1. Install WireGuard from the Google Play Store.
2. Download the configuration from the IT Self-Service Portal.
3. Open WireGuard, tap **+**, and select **Import from file or archive**.
4. Select the downloaded file and toggle the tunnel on.

---

## 4. Split Tunneling Policy

4.1. **Default Configuration:** The Acme Corp VPN uses **split tunneling** by default. This means:
   - Traffic destined for Acme Corp internal networks (10.0.0.0/8, 172.16.0.0/12) is routed through the VPN.
   - All other internet traffic (web browsing, streaming, personal apps) goes directly through your local internet connection.

4.2. **Full Tunnel Mode:** Employees handling Confidential or Restricted data must use full tunnel mode. Contact IT to receive a full-tunnel configuration file.

4.3. **DNS:** All DNS queries are routed through the VPN to prevent DNS leaks and ensure access to internal hostnames (*.acmecorp.internal).

---

## 5. Auto-Connect Rules

5.1. **On-Demand Connect:** Configure your VPN client to auto-connect when accessing internal domains. WireGuard supports on-demand activation rules.

5.2. **Trusted Networks:** The VPN is not required when connected to the Acme Corp office Wi-Fi networks (SSID: `AcmeCorp-Secure` or `AcmeCorp-Engineering`). The VPN client should be configured to disconnect automatically on trusted networks.

5.3. **Untrusted Networks:** The VPN should auto-connect when joining any network not in the trusted list. This is especially important for hotel, airport, and coffee shop Wi-Fi.

---

## 6. Troubleshooting

### 6.1. Cannot Connect

- **Check credentials:** Ensure your Okta account is not locked. Try logging in at https://acmecorp.okta.com.
- **Check MFA:** Ensure your MFA device is available and has battery.
- **Restart the client:** Quit and reopen WireGuard or Tunnelblick.
- **Check internet:** Confirm you have a working internet connection without VPN.
- **Firewall/ISP blocking:** Some networks block WireGuard (UDP 51820). Try OpenVPN (TCP 443) as a fallback.

### 6.2. Connection Drops Frequently

- **Switch protocols:** If WireGuard is unstable, try OpenVPN TCP mode.
- **Wi-Fi interference:** Move closer to your router or switch to a wired (Ethernet) connection.
- **MTU issues:** Try reducing MTU in the WireGuard config:
  ```
  [Interface]
  MTU = 1280
  ```
- **Power saving:** Disable Wi-Fi power saving on your OS. On macOS, uncheck "Low Data Mode" for your Wi-Fi network in System Settings.
- **Keep-alive:** Ensure PersistentKeepalive is set in your config (default: 25 seconds).

### 6.3. Slow Performance

- **Check routing:** Ensure split tunneling is active. Full tunnel mode routes all traffic through the VPN, which is slower.
- **Server selection:** The VPN auto-selects the nearest server. If performance is poor, contact IT to check server load.
- **Bandwidth:** Run a speed test at https://speedtest.acmecorp.com both with and without VPN. Report results to IT if VPN speeds are less than 50% of your base speed.

### 6.4. Internal Sites Not Loading

- **DNS flush:** Clear your DNS cache:
  ```
  # macOS
  sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

  # Windows
  ipconfig /flushdns

  # Linux
  sudo systemd-resolve --flush-caches
  ```
- **Check VPN status:** Verify the VPN tunnel is active and you have an assigned IP (10.x.x.x range).
- **Browser cache:** Try accessing the site in an incognito/private window.

---

## 7. Known Issues

| Issue | Status | Workaround |
|---|---|---|
| WireGuard disconnects on macOS Sequoia after sleep | Investigating | Toggle tunnel off/on after waking from sleep |
| OpenVPN slow on Windows 11 24H2 | Patch pending | Use WireGuard instead |
| iOS WireGuard drains battery on cellular | By design | Disconnect VPN when not actively using internal resources |
| Split tunnel DNS leak on some Linux distros | Documented | Use `resolvconf` or `systemd-resolved` integration |

---

## 8. Emergency Access

8.1. **If VPN is completely down:** In case of a VPN infrastructure outage, IT will activate the emergency access gateway at https://emergency.acmecorp.com. This provides browser-based access to critical systems (email, Slack, Jira) without VPN.

8.2. **Notification:** VPN outages are communicated via:
   - SMS alert to all employees (via PagerDuty)
   - Email to all-staff@acmecorp.com
   - Status page: https://status.acmecorp.com

8.3. **On-Call:** The Infrastructure On-Call team is available 24/7 for VPN emergencies. Reach them via PagerDuty or by calling +1 (555) 012-7890.

---

## 9. Security Reminders

- Never share your VPN configuration file with anyone.
- Report any suspected VPN compromise to security@acmecorp.com immediately.
- Do not use personal VPN services (NordVPN, ExpressVPN, etc.) simultaneously with the corporate VPN.
- Keep your VPN client updated to the latest version.
- The VPN logs connection timestamps and data volumes for security auditing. No traffic content is inspected.

---

## 10. Contact & Support

- **VPN Issues:** Slack #vpn-support
- **IT Help Desk:** it-support@acmecorp.com or Slack #it-helpdesk
- **Emergency (24/7):** +1 (555) 012-7890
- **Self-Service Portal:** https://itportal.acmecorp.com/vpn
- **VPN Status:** https://status.acmecorp.com

---

*Configuration files are rotated every 90 days. You will receive an email reminder 14 days before your current configuration expires.*
