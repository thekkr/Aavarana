# DNS Notes for aavarana.com

## To REVERT back to GoDaddy parking page

Go to GoDaddy → My Products → aavarana.com → DNS → Nameservers → Change → Enter my own nameservers:

```
ns1.dns-parking.com
ns2.dns-parking.com
```

Save. Wait 5-30 minutes. Parking page will be back.

---

## Current Cloudflare nameservers (active setup)

```
alaric.ns.cloudflare.com
oaklyn.ns.cloudflare.com
```

---

## DNS records found before Cloudflare setup (for reference)

| Type  | Name       | Content              | Purpose              |
|-------|------------|----------------------|----------------------|
| A     | aavarana.com | 34.120.137.41      | Old web hosting (Hostinger) |
| AAAA  | aavarana.com | 2600:1901:0:84...  | Old web hosting IPv6 |
| CNAME | www        | connect.hosting...   | Hostinger web        |
| CNAME | hostingerm | hostingermail-a...   | Hostinger email      |
| CNAME | hostingerm | hostingermail-b...   | Hostinger email      |
| CNAME | hostingerm | hostingermail-c...   | Hostinger email      |
| MX    | aavarana.com | mx1.hostinge...    | Email routing        |
| MX    | aavarana.com | mx2.hostinge...    | Email routing        |
| TXT   | aavarana.com | "v=spf1 include:.. | Email SPF record     |
