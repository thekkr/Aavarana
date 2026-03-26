# Deploying Aavarana — Gunicorn + Cloudflare

This guide covers deploying on a Linux server (Ubuntu/Debian) with Gunicorn as the
application server and Cloudflare as the DNS/proxy/SSL layer.

---

## Prerequisites

- A Linux server (VPS, cloud instance, or Android via Termux)
- A domain name pointed to your server's IP
- Python 3.11+ installed
- Git installed
- Cloudflare account with your domain added

---

## Step 1 — Clone the Project

```bash
cd /home/<your-user>
git clone https://github.com/thekkr/Aavarana.git
cd Aavarana
```

---

## Step 2 — Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## Step 3 — Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Fill in the following values:

```env
SECRET_KEY=<generate one — see below>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
```

**Generate a secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 4 — Run Django Setup

```bash
export DJANGO_SETTINGS_MODULE=aavarana.settings.prod

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

> `createsuperuser` will prompt for username, email, and password.
> This account will be the only Superuser on the site.

---

## Step 5 — Test Gunicorn

```bash
gunicorn aavarana.wsgi:application --bind 0.0.0.0:8000
```

Visit `http://<your-server-ip>:8000` — if the site loads, Gunicorn is working.
Stop it with `Ctrl+C` before proceeding.

---

## Step 6 — Run Gunicorn as a Background Service

Create a systemd service so Gunicorn starts automatically on reboot:

```bash
sudo nano /etc/systemd/system/aavarana.service
```

Paste the following (replace `<your-user>` with your Linux username):

```ini
[Unit]
Description=Aavarana Gunicorn
After=network.target

[Service]
User=<your-user>
Group=www-data
WorkingDirectory=/home/<your-user>/Aavarana
Environment="DJANGO_SETTINGS_MODULE=aavarana.settings.prod"
EnvironmentFile=/home/<your-user>/Aavarana/.env
ExecStart=/home/<your-user>/Aavarana/.venv/bin/gunicorn \
    aavarana.wsgi:application \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --access-logfile /home/<your-user>/Aavarana/logs/access.log \
    --error-logfile /home/<your-user>/Aavarana/logs/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Create the logs directory and start the service:

```bash
mkdir -p /home/<your-user>/Aavarana/logs
sudo systemctl daemon-reload
sudo systemctl enable aavarana
sudo systemctl start aavarana
sudo systemctl status aavarana
```

---

## Step 7 — Install and Configure Nginx

Gunicorn serves the app but Nginx handles static files, media, and forwards traffic to Gunicorn.

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/aavarana
```

Paste:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /home/<your-user>/Aavarana/staticfiles/;
    }

    location /media/ {
        alias /home/<your-user>/Aavarana/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/aavarana /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 8 — Configure Cloudflare

### 8.1 — Add DNS Record

In Cloudflare dashboard → your domain → DNS:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `<your server IP>` | Proxied (orange cloud) |
| A | `www` | `<your server IP>` | Proxied (orange cloud) |

### 8.2 — SSL/TLS Mode

Go to **SSL/TLS → Overview** and set mode to:

```
Full (strict)
```

> Do NOT use "Flexible" — it sends traffic to your server over plain HTTP which defeats HTTPS.

### 8.3 — Enable HTTPS Redirect

Go to **SSL/TLS → Edge Certificates**:
- Turn on **Always Use HTTPS**
- Turn on **Automatic HTTPS Rewrites**

### 8.4 — Add Security Headers (optional but recommended)

Go to **Rules → Transform Rules → Modify Response Header** and add:

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

---

## Step 9 — Update Google OAuth Redirect URI

In Google Cloud Console → APIs & Services → Credentials → your OAuth Client:

Add to **Authorized redirect URIs**:
```
https://yourdomain.com/accounts/social/google/login/callback/
```

Also update **Authorized JavaScript origins**:
```
https://yourdomain.com
```

---

## Step 10 — Verify Everything

```bash
# Check Gunicorn is running
sudo systemctl status aavarana

# Check Nginx is running
sudo systemctl status nginx

# Check logs if something is wrong
tail -f /home/<your-user>/Aavarana/logs/error.log
sudo tail -f /var/log/nginx/error.log
```

Visit `https://yourdomain.com` — the site should load over HTTPS.

---

## Updating the Site After Code Changes

```bash
cd /home/<your-user>/Aavarana
source .venv/bin/activate
git pull
pip install -r requirements.txt          # only needed if requirements changed
export DJANGO_SETTINGS_MODULE=aavarana.settings.prod
python manage.py migrate                 # only needed if models changed
python manage.py collectstatic --noinput
sudo systemctl restart aavarana
```

---

## Termux (Android) Specific Notes

If running on Android via Termux, systemd is not available. Use this instead:

**Start Gunicorn manually:**
```bash
cd ~/Aavarana
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=aavarana.settings.prod
gunicorn aavarana.wsgi:application --workers 2 --bind 0.0.0.0:8000 --daemon
```

**Stop Gunicorn:**
```bash
pkill gunicorn
```

**Nginx on Termux:**
```bash
pkg install nginx
```

Configure the same Nginx block as Step 7 in `$PREFIX/etc/nginx/nginx.conf`.

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| 502 Bad Gateway | Gunicorn not running — `systemctl status aavarana` |
| Static files not loading | Run `collectstatic`, check Nginx `alias` path |
| Google login broken | Check redirect URI in Google Cloud Console |
| `ALLOWED_HOSTS` error | Add your domain to `.env` `ALLOWED_HOSTS=` |
| Database errors | Run `python manage.py migrate` |
| Permission denied on media/ | `sudo chown -R <your-user>:www-data media/` |
