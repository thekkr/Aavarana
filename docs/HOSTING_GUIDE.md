# Aavarana Local Hosting Guide

## Overview

The website runs on your PC and is publicly accessible via Cloudflare Tunnel.
Friends access it at: **https://aavarana.com**

---

## Every Time You Want to Host

### Step 1 — Start Django (Waitress)

Open a terminal and run:

```bash
cd C:\Users\Masterigs\Aavarana
set DJANGO_SETTINGS_MODULE=aavarana.settings.prod
waitress-serve --host=127.0.0.1 --port=8000 aavarana.wsgi:application
```

Expected output:
```
INFO:waitress:Serving on http://127.0.0.1:8000
```

### Step 2 — Start Cloudflare Tunnel

Open a **second terminal** and run:

```bash
cloudflared tunnel run aavarana
```

Expected output (last lines):
```
INF Registered tunnel connection connIndex=0 ... location=blr02 protocol=quic
INF Registered tunnel connection connIndex=1 ... location=bom12 protocol=quic
```

### Step 3 — Verify

- Open your phone browser and go to `https://aavarana.com`
- Site should load within a few seconds

---

## Mandatory Checks Before Sharing with Friends

- [ ] Waitress terminal shows `Serving on http://127.0.0.1:8000`
- [ ] Cloudflare tunnel shows `Registered tunnel connection`
- [ ] Site loads on phone at `https://aavarana.com`
- [ ] Google login works on phone
- [ ] Your PC stays ON (site goes down if PC sleeps/shuts down)

---

## Troubleshooting

### Site not loading (`DNS_PROBE_FINISHED_NXDOMAIN`)
- DNS cache issue on your PC — site works for everyone else
- Flush DNS: `ipconfig /flushdns`
- Test on your phone instead

### Internal Server Error
- Check that `DJANGO_SETTINGS_MODULE` is set correctly
- Always use `set DJANGO_SETTINGS_MODULE=aavarana.settings.prod` before waitress

### Google Login Error (`redirect_uri_mismatch`)
- Make sure waitress was started with `set DJANGO_SETTINGS_MODULE=aavarana.settings.prod`
- The authorized redirect URI in Google Console must be:
  `https://aavarana.com/accounts/social/google/login/callback/`

### Site goes down
- Check if your PC went to sleep — disable sleep mode while hosting
- Restart both waitress and cloudflared tunnel

---

## To Revert to Parking Page

Go to GoDaddy → My Products → aavarana.com → DNS → Nameservers → Change → Enter my own nameservers:

```
ns1.dns-parking.com
ns2.dns-parking.com
```

Save. Wait 5-30 minutes. Parking page returns.

---

## Key Configuration

| Setting | Value |
|---------|-------|
| Public URL | https://aavarana.com |
| Local server | http://127.0.0.1:8000 |
| Tunnel name | aavarana |
| Tunnel ID | d6daee28-5fca-45da-a065-a34316d3c669 |
| Settings module | aavarana.settings.prod |
| Cloudflare nameservers | alaric.ns.cloudflare.com, oaklyn.ns.cloudflare.com |
| Google OAuth callback | https://aavarana.com/accounts/social/google/login/callback/ |

---

## Cloudflare Dashboard

- DNS records: cloudflare.com → aavarana.com → DNS
- Tunnel status: cloudflare.com → Zero Trust → Networks → Tunnels

---

## Google Cloud Console

- OAuth credentials: console.cloud.google.com → APIs & Services → Credentials
- OAuth consent: console.cloud.google.com → APIs & Services → OAuth consent screen → Audience
