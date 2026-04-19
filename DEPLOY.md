# 🚀 Voyager — Deployment Guide

Deploy your travel planner to the internet in **under 5 minutes** for free.

---

## ⚡ Option 1 — Render.com (Recommended · Completely Free)

### Step 1 — Push to GitHub
```bash
# In this folder (voyager-prod/)
git init
git add .
git commit -m "Voyager Travel Planner"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/voyager.git
git push -u origin main
```

### Step 2 — Deploy on Render
1. Go to **https://render.com** → Sign up free
2. Click **New +** → **Web Service**
3. Connect your GitHub → select `voyager` repo
4. Render auto-detects the settings from `render.yaml`:

| Setting | Value |
|---------|-------|
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` |

5. Click **Create Web Service**
6. Wait ~2 minutes → your app is live at:
   `https://voyager-travel-planner.onrender.com`

> **Free tier note:** App sleeps after 15 min inactivity. First load after sleep takes ~30 sec. Upgrade to $7/mo for always-on.

---

## ⚡ Option 2 — Railway.app (Free · $5 credit/month)

### Step 1 — Push to GitHub (same as above)

### Step 2 — Deploy on Railway
1. Go to **https://railway.app** → Sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `voyager` repo
4. Railway reads `railway.toml` and `Procfile` automatically
5. Done in ~90 seconds → click the generated URL

---

## ⚡ Option 3 — Heroku (Paid · $5/month)

```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
heroku login
heroku create voyager-travel-planner
git push heroku main
heroku open
```

---

## ⚡ Option 4 — PythonAnywhere (Free tier)

1. Sign up at **https://www.pythonanywhere.com**
2. Go to **Files** → upload entire project folder
3. Open **Bash console**:
```bash
pip3 install flask gunicorn --user
```
4. Go to **Web** tab → **Add a new web app** → **Manual config** → Python 3.12
5. Set **Source code**: `/home/yourusername/voyager-prod`
6. Edit the WSGI file:
```python
import sys
sys.path.insert(0, '/home/yourusername/voyager-prod')
from app import app as application
```
7. **Reload** → your app is live at `yourusername.pythonanywhere.com`

---

## ⚡ Option 5 — Docker (Any VPS / Cloud)

```bash
# Build
docker build -t voyager .

# Run locally
docker run -p 5000:5000 -v voyager_data:/data voyager

# Push to Docker Hub and run on any server
docker tag voyager yourusername/voyager
docker push yourusername/voyager

# On your VPS:
docker pull yourusername/voyager
docker run -d -p 80:5000 -v voyager_data:/data --restart always yourusername/voyager
```

---

## ⚡ Option 6 — Ubuntu VPS (DigitalOcean / AWS / Hetzner)

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Upload project
scp -r voyager-prod/ user@your-server-ip:/opt/voyager

# 3. Install dependencies
cd /opt/voyager
pip3 install -r requirements.txt

# 4. Create systemd service
sudo nano /etc/systemd/system/voyager.service
```

Paste:
```ini
[Unit]
Description=Voyager Travel Planner
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/voyager
Environment=PORT=5000
Environment=DB_PATH=/opt/voyager/voyager.db
ExecStart=/usr/local/bin/gunicorn app:app --bind 0.0.0.0:5000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 5. Start service
sudo systemctl daemon-reload
sudo systemctl enable voyager
sudo systemctl start voyager

# 6. Nginx reverse proxy
sudo apt install nginx
sudo nano /etc/nginx/sites-available/voyager
```

Paste:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your IP

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/voyager /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Add free SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Port to listen on (auto-set by all platforms) |
| `DB_PATH` | `./voyager.db` | SQLite database file path |

---

## 📧 Add Real Email OTP (Production)

Open `app.py` and replace the `_log_otp()` call with actual email sending:

```python
import smtplib
from email.mime.text import MIMEText

def send_otp_email(to_email, otp):
    msg = MIMEText(
        f"Your Voyager verification code is:\n\n"
        f"  {otp}\n\n"
        f"This code expires in 10 minutes. Do not share it."
    )
    msg["Subject"] = f"Voyager — {otp} is your code"
    msg["From"]    = os.environ.get("SMTP_FROM", "noreply@yourdomain.com")
    msg["To"]      = to_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
        print(f"[Email] OTP sent to {to_email}")
    except Exception as e:
        print(f"[Email] Failed: {e}")
```

Add to environment variables: `SMTP_USER=your@gmail.com`, `SMTP_PASS=your-app-password`

> For Gmail: enable 2FA → generate an **App Password** at myaccount.google.com/apppasswords

---

## ✅ Verify Deployment

After deploying, test these URLs in your browser:

```
https://your-app.onrender.com/          → Should load the Voyager UI
https://your-app.onrender.com/api/me    → Should return {"ok":false,"error":"Authentication required"}
```

Both working = deployment successful! 🎉
