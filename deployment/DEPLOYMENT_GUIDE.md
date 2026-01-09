# Carbon Room Deployment Guide

**Domain:** thecarbon6.agency
**Platform:** SiteGround (cPanel with Python/Passenger)
**Application:** FastAPI Python

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [SiteGround Setup](#siteground-setup)
3. [SSH Connection](#ssh-connection)
4. [Python Virtual Environment](#python-virtual-environment)
5. [File Upload](#file-upload)
6. [Passenger Configuration](#passenger-configuration)
7. [Environment Variables](#environment-variables)
8. [SSL Certificate](#ssl-certificate)
9. [Testing Deployment](#testing-deployment)
10. [Troubleshooting](#troubleshooting)
11. [Backup Deployment (Render)](#backup-deployment-render)

---

## Prerequisites

Before deploying, ensure you have:

- [ ] SiteGround hosting account with Python support
- [ ] Domain thecarbon6.agency pointed to SiteGround nameservers
- [ ] SSH access enabled in SiteGround cPanel
- [ ] SFTP client (FileZilla, Cyberduck) or Git
- [ ] Local copy of Carbon Room application

---

## SiteGround Setup

### Step 1: Access cPanel

1. Log into SiteGround Client Area
2. Navigate to **Websites** > **Site Tools**
3. Select thecarbon6.agency domain

### Step 2: Enable SSH Access

1. Go to **Devs** > **SSH Keys Manager**
2. Generate or import your SSH public key
3. Note the SSH connection details:
   ```
   Host: ssh.thecarbon6.agency (or IP from Site Tools)
   Port: 18765 (SiteGround custom port)
   Username: [your-cpanel-username]
   ```

### Step 3: Create Python Application

1. Go to **Devs** > **App Manager**
2. Click **Create Application**
3. Select:
   - **Python** as application type
   - **Python 3.9** (or highest available)
   - **Application Root:** thecarbon6.agency
   - **Application URL:** Leave as `/`
   - **Startup File:** `passenger_wsgi.py`

---

## SSH Connection

### Connect via SSH

```bash
# Standard SSH connection
ssh -p 18765 username@your-server-ip

# Or using SSH config (~/.ssh/config)
Host siteground
    HostName your-server-ip
    Port 18765
    User username
    IdentityFile ~/.ssh/your_private_key
```

### Verify Connection

```bash
# After connecting, check Python version
python3 --version

# Check current directory
pwd
# Should show: /home/username
```

---

## Python Virtual Environment

### Step 1: Navigate to Application Directory

```bash
cd ~/thecarbon6.agency
```

### Step 2: Create Virtual Environment (if not auto-created)

```bash
# Check if virtualenv exists
ls ~/virtualenv/thecarbon6.agency/

# If not, create it manually
python3 -m venv ~/virtualenv/thecarbon6.agency/3.9
```

### Step 3: Activate Virtual Environment

```bash
source ~/virtualenv/thecarbon6.agency/3.9/bin/activate
```

### Step 4: Upgrade pip

```bash
pip install --upgrade pip
```

---

## File Upload

### Option A: SFTP Upload

1. Connect via SFTP:
   ```
   Host: your-server-ip
   Port: 18765
   Protocol: SFTP
   User: username
   ```

2. Navigate to `/home/username/thecarbon6.agency/`

3. Upload these files and directories:
   ```
   thecarbon6.agency/
   ├── api/
   │   └── server.py
   ├── templates/
   │   ├── admin.html
   │   └── user.html
   ├── static/
   │   └── (static files)
   ├── vault/
   ├── passenger_wsgi.py
   ├── requirements.txt
   ├── .htaccess
   └── .env
   ```

### Option B: Git Clone

```bash
# SSH into server first
cd ~/thecarbon6.agency

# Clone repository (if using Git)
git clone https://github.com/your-org/carbon-room.git .

# Or pull latest changes
git pull origin main
```

### Option C: SCP Upload

```bash
# From local machine
scp -P 18765 -r ./deployment/* username@server-ip:~/thecarbon6.agency/
scp -P 18765 -r ./api username@server-ip:~/thecarbon6.agency/
scp -P 18765 -r ./templates username@server-ip:~/thecarbon6.agency/
scp -P 18765 -r ./static username@server-ip:~/thecarbon6.agency/
```

---

## Passenger Configuration

### Step 1: Install Dependencies

```bash
# Ensure virtualenv is activated
source ~/virtualenv/thecarbon6.agency/3.9/bin/activate

# Navigate to app directory
cd ~/thecarbon6.agency

# Install requirements
pip install -r requirements.txt
```

### Step 2: Configure .htaccess

Edit `.htaccess` and replace `username` with your actual cPanel username:

```apache
PassengerAppRoot /home/YOUR_USERNAME/thecarbon6.agency
PassengerBaseURI /
PassengerPython /home/YOUR_USERNAME/virtualenv/thecarbon6.agency/3.9/bin/python
```

### Step 3: Verify passenger_wsgi.py

Ensure `passenger_wsgi.py` is in the root directory:

```bash
ls -la ~/thecarbon6.agency/passenger_wsgi.py
```

### Step 4: Create Required Directories

```bash
mkdir -p ~/thecarbon6.agency/vault
mkdir -p ~/thecarbon6.agency/telemetry
chmod 750 ~/thecarbon6.agency/vault
chmod 750 ~/thecarbon6.agency/telemetry
```

### Step 5: Restart Application

In SiteGround Site Tools:
1. Go to **Devs** > **App Manager**
2. Find your Python application
3. Click **Restart**

Or via SSH:
```bash
touch ~/thecarbon6.agency/tmp/restart.txt
```

---

## Environment Variables

### Step 1: Create .env File

```bash
cd ~/thecarbon6.agency
cp .env.production .env
```

### Step 2: Generate Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -base64 32

# Generate API_KEY
openssl rand -hex 16

# Generate ENCRYPTION_KEY (using Python)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 3: Edit .env with Real Values

```bash
nano .env
```

Replace all `CHANGE_ME_*` placeholders with generated keys.

### Step 4: Secure .env File

```bash
chmod 600 .env
```

---

## SSL Certificate

### Automatic SSL (Let's Encrypt)

SiteGround provides free Let's Encrypt certificates:

1. Go to **Security** > **SSL Manager**
2. Select thecarbon6.agency
3. Click **Get Free SSL**
4. Wait for certificate issuance (usually < 5 minutes)

### Enable HTTPS Redirect

After SSL is active, uncomment HSTS header in `.htaccess`:

```apache
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
```

### Force HTTPS

Verify this section is in `.htaccess`:

```apache
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

---

## Testing Deployment

### Step 1: Health Check

```bash
# From local machine
curl -I https://thecarbon6.agency/

# Expected: HTTP/2 200 or redirect to /admin
```

### Step 2: API Documentation

Visit: `https://thecarbon6.agency/docs`

You should see the FastAPI Swagger UI.

### Step 3: Admin Dashboard

Visit: `https://thecarbon6.agency/admin`

### Step 4: Test API Endpoints

```bash
# List protocols
curl https://thecarbon6.agency/api/protocols

# Get stats
curl https://thecarbon6.agency/api/stats
```

### Step 5: Check Logs

```bash
# SSH into server
tail -f ~/thecarbon6.agency/logs/error.log
tail -f ~/logs/thecarbon6.agency.error.log
```

---

## Troubleshooting

### Common Issues

#### 1. 503 Service Unavailable

**Cause:** Passenger cannot start Python application

**Solution:**
```bash
# Check Passenger logs
cat ~/logs/thecarbon6.agency.error.log

# Verify Python path in .htaccess
which python3

# Ensure all dependencies installed
source ~/virtualenv/thecarbon6.agency/3.9/bin/activate
pip list
```

#### 2. Import Errors

**Cause:** Missing dependencies or wrong Python version

**Solution:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### 3. Static Files Not Loading

**Cause:** Incorrect static file mounting

**Solution:**
Ensure `static/` directory exists and has correct permissions:
```bash
chmod -R 755 ~/thecarbon6.agency/static
```

#### 4. Permission Denied

**Cause:** File permissions too restrictive

**Solution:**
```bash
chmod 755 ~/thecarbon6.agency
chmod 755 ~/thecarbon6.agency/api
chmod 644 ~/thecarbon6.agency/api/server.py
chmod 644 ~/thecarbon6.agency/passenger_wsgi.py
```

#### 5. Environment Variables Not Loading

**Cause:** .env file not being read

**Solution:**
Add python-dotenv to passenger_wsgi.py or load manually:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Debug Mode

Temporarily enable debug logging:

```bash
# Edit .env
nano .env
# Set: DEBUG=true, LOG_LEVEL=DEBUG

# Restart app
touch ~/thecarbon6.agency/tmp/restart.txt
```

---

## Backup Deployment (Render)

If SiteGround deployment fails, use Render as backup:

### Step 1: Create render.yaml

Already included in `deployment/render.yaml`

### Step 2: Connect GitHub Repository

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New** > **Web Service**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`

### Step 3: Configure Environment Variables

Add in Render dashboard:
- `ENV=production`
- `SECRET_KEY=your-secret`
- `BASE_URL=https://carbon-room.onrender.com`

### Step 4: Deploy

Click **Create Web Service**

---

## Maintenance

### Regular Tasks

```bash
# Update dependencies monthly
pip install --upgrade -r requirements.txt

# Rotate logs
find ~/logs -name "*.log" -mtime +30 -delete

# Backup vault
tar -czf ~/backups/vault_$(date +%Y%m%d).tar.gz ~/thecarbon6.agency/vault
```

### Monitoring

Set up uptime monitoring:
- [UptimeRobot](https://uptimerobot.com) - Free tier available
- [Better Uptime](https://betteruptime.com)

Monitor endpoint: `https://thecarbon6.agency/api/stats`

---

## Quick Commands Reference

```bash
# SSH into SiteGround
ssh -p 18765 username@server-ip

# Activate virtualenv
source ~/virtualenv/thecarbon6.agency/3.9/bin/activate

# Restart application
touch ~/thecarbon6.agency/tmp/restart.txt

# View error logs
tail -f ~/logs/thecarbon6.agency.error.log

# Check running processes
ps aux | grep python

# Test locally before deploy
uvicorn api.server:app --host 0.0.0.0 --port 8003
```

---

## Support

- **SiteGround Support:** 24/7 via Site Tools > Help Center
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Passenger Docs:** https://www.phusionpassenger.com/docs/

---

*Document Version: 1.0.0*
*Last Updated: 2026-01-09*
*Prepared by: OPS-V (VLTRN Operations)*
