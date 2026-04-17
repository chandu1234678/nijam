# 🗺️ AWS Deployment Flowchart - Nijam Fact Checker

## Visual Deployment Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS DEPLOYMENT PROCESS                        │
│                     Total Time: ~60 minutes                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: AWS SETUP (25 minutes)                                 │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Create AWS      │
    │  Account         │
    │  (if needed)     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Create RDS      │
    │  PostgreSQL      │
    │  (15 min)        │
    │                  │
    │  • db.t2.micro   │
    │  • PostgreSQL 15 │
    │  • 20 GB storage │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Save RDS        │
    │  Endpoint        │
    │  & Password      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Launch EC2      │
    │  Instance        │
    │  (10 min)        │
    │                  │
    │  • t2.micro      │
    │  • Ubuntu 22.04  │
    │  • 30 GB storage │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Configure       │
    │  Security Groups │
    │                  │
    │  • SSH (22)      │
    │  • HTTP (80)     │
    │  • HTTPS (443)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Download        │
    │  Key Pair        │
    │  (nijam-key.pem) │
    └────────┬─────────┘
             │
             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: SERVER SETUP (20 minutes)                              │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  SSH into EC2    │
    │                  │
    │  ssh -i key.pem  │
    │  ubuntu@EC2_IP   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Run Setup       │
    │  Script          │
    │                  │
    │  ./aws_setup.sh  │
    └────────┬─────────┘
             │
             ├─────────────────────────────────────────┐
             │                                         │
             ▼                                         ▼
    ┌──────────────────┐                    ┌──────────────────┐
    │  Install System  │                    │  Clone GitHub    │
    │  Packages        │                    │  Repository      │
    │                  │                    │                  │
    │  • Python 3.11   │                    │  git clone       │
    │  • Nginx         │                    │  nijam.git       │
    │  • PostgreSQL    │                    └────────┬─────────┘
    └────────┬─────────┘                             │
             │                                       │
             └───────────────┬───────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Setup Python    │
                    │  Virtual Env     │
                    │                  │
                    │  python3.11 -m   │
                    │  venv venv       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Install         │
                    │  Dependencies    │
                    │                  │
                    │  pip install -r  │
                    │  requirements.txt│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Setup Systemd   │
                    │  Service         │
                    │                  │
                    │  nijam.service   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Setup Nginx     │
                    │  Reverse Proxy   │
                    │                  │
                    │  /etc/nginx/...  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Setup Swap      │
                    │  (2GB)           │
                    │                  │
                    │  For memory      │
                    │  safety          │
                    └────────┬─────────┘
                             │
                             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: CONFIGURATION (10 minutes)                             │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Edit .env File  │
    │                  │
    │  nano .env       │
    └────────┬─────────┘
             │
             ├─────────────────────────────────────────┐
             │                                         │
             ▼                                         ▼
    ┌──────────────────┐                    ┌──────────────────┐
    │  Add Database    │                    │  Add API Keys    │
    │  URL             │                    │                  │
    │                  │                    │  • CEREBRAS      │
    │  DATABASE_URL=   │                    │  • GROQ          │
    │  postgresql://   │                    │  • GEMINI        │
    │  ...             │                    │  • NEWS_API      │
    └────────┬─────────┘                    │  • TAVILY        │
             │                              │  • SERPAPI       │
             │                              └────────┬─────────┘
             │                                       │
             └───────────────┬───────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Generate JWT    │
                    │  Secret          │
                    │                  │
                    │  openssl rand    │
                    │  -hex 32         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Configure Model │
                    │  Settings        │
                    │                  │
                    │  DEBERTA_MODEL=  │
                    │  (empty for      │
                    │  TF-IDF only)    │
                    └────────┬─────────┘
                             │
                             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: DATABASE INITIALIZATION (5 minutes)                    │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Activate Venv   │
    │                  │
    │  source venv/    │
    │  bin/activate    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Test Database   │
    │  Connection      │
    │                  │
    │  psql $DB_URL    │
    │  -c "SELECT 1;"  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Run Migrations  │
    │                  │
    │  alembic upgrade │
    │  head            │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Verify Tables   │
    │  Created         │
    │                  │
    │  psql $DB_URL    │
    │  -c "\dt"        │
    └────────┬─────────┘
             │
             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: START SERVICES (2 minutes)                             │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Start Nijam     │
    │  Service         │
    │                  │
    │  systemctl start │
    │  nijam           │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Start Nginx     │
    │                  │
    │  systemctl start │
    │  nginx           │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Check Status    │
    │                  │
    │  systemctl       │
    │  status nijam    │
    └────────┬─────────┘
             │
             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: TESTING & VERIFICATION (3 minutes)                     │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Test Local      │
    │  Health          │
    │                  │
    │  curl localhost: │
    │  8000/health     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Test Public     │
    │  Health          │
    │                  │
    │  curl EC2_IP/    │
    │  health          │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Test Fact Check │
    │                  │
    │  POST /message   │
    │  with test claim │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Run Stress Test │
    │                  │
    │  python tests/   │
    │  stress_test.py  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Check Logs      │
    │                  │
    │  journalctl -u   │
    │  nijam -f        │
    └────────┬─────────┘
             │
             ▼

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: EXTENSION UPDATE (5 minutes)                           │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Update          │
    │  config.js       │
    │                  │
    │  API_BASE_URL =  │
    │  EC2_IP or       │
    │  domain          │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Reload          │
    │  Extension       │
    │                  │
    │  chrome://       │
    │  extensions      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Test Extension  │
    │                  │
    │  • Fact check    │
    │  • Image upload  │
    │  • Viral detect  │
    └────────┬─────────┘
             │
             ▼

┌─────────────────────────────────────────────────────────────────┐
│ ✅ DEPLOYMENT COMPLETE!                                         │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Monitor for     │
    │  24 Hours        │
    │                  │
    │  • Check logs    │
    │  • Monitor RAM   │
    │  • Test features │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Setup Optional  │
    │  Features        │
    │                  │
    │  • SSL/HTTPS     │
    │  • CloudWatch    │
    │  • Custom domain │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  🎉 PRODUCTION   │
    │     READY!       │
    └──────────────────┘
```

---

## Decision Tree: Troubleshooting

```
                    ┌──────────────────┐
                    │  Deployment      │
                    │  Issue?          │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Can't    │  │ Database │  │ Service  │
        │ Connect  │  │ Error    │  │ Won't    │
        │ to EC2   │  │          │  │ Start    │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Check    │  │ Check    │  │ Check    │
        │ Security │  │ RDS SG   │  │ Logs     │
        │ Group    │  │ & URL    │  │          │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Verify   │  │ Test     │  │ journalctl│
        │ Key      │  │ psql     │  │ -u nijam │
        │ Perms    │  │ connect  │  │ -n 50    │
        └──────────┘  └──────────┘  └──────────┘
```

---

## Resource Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEM ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Internet   │
    │   Users      │
    └──────┬───────┘
           │
           │ HTTPS (443)
           │
           ▼
    ┌──────────────┐
    │   Nginx      │
    │   Reverse    │
    │   Proxy      │
    └──────┬───────┘
           │
           │ HTTP (8000)
           │
           ▼
    ┌──────────────┐
    │   FastAPI    │
    │   Backend    │
    │   (Uvicorn)  │
    └──────┬───────┘
           │
           ├─────────────────┬─────────────────┬─────────────────┐
           │                 │                 │                 │
           ▼                 ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐    ┌──────────┐      ┌──────────┐
    │ RDS      │      │ TF-IDF   │    │ External │      │ Redis    │
    │ Postgres │      │ Model    │    │ APIs     │      │ Cache    │
    │          │      │          │    │          │      │ (opt)    │
    │ • Users  │      │ • 96.63% │    │ • Gemini │      │          │
    │ • Checks │      │   Acc    │    │ • Groq   │      │ • ML     │
    │ • Velocity│     │ • 200MB  │    │ • News   │      │   Cache  │
    └──────────┘      └──────────┘    └──────────┘      └──────────┘
```

---

## Memory Usage Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│              t2.micro RAM USAGE (1 GB Total)                    │
└─────────────────────────────────────────────────────────────────┘

    Total: 1024 MB
    
    ┌────────────────────────────────────────────────┐
    │ System (Ubuntu)                    ~200 MB     │ ████████
    ├────────────────────────────────────────────────┤
    │ Python + FastAPI                   ~150 MB     │ ██████
    ├────────────────────────────────────────────────┤
    │ TF-IDF Model                       ~200 MB     │ ████████
    ├────────────────────────────────────────────────┤
    │ Database Connections               ~50 MB      │ ██
    ├────────────────────────────────────────────────┤
    │ Nginx                              ~20 MB      │ █
    ├────────────────────────────────────────────────┤
    │ Available / Buffer                 ~404 MB     │ ████████████████
    └────────────────────────────────────────────────┘
    
    ✅ Safe: 400+ MB available for spikes
    
    Swap: 2 GB (for safety)
```

---

## Cost Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS COST TIMELINE                             │
└─────────────────────────────────────────────────────────────────┘

Month 1-12 (Free Tier):
    ┌────────────────────────────────────────────────┐
    │ $0/month                                       │ ✅ FREE
    └────────────────────────────────────────────────┘

Month 13+ (After Free Tier):
    ┌────────────────────────────────────────────────┐
    │ EC2 t2.micro:        $8.50                     │ ████
    │ RDS db.t2.micro:     $15.00                    │ ███████
    │ Storage:             $3.00                     │ █
    │ Data Transfer:       $1.00                     │ █
    ├────────────────────────────────────────────────┤
    │ Total:               ~$27.50/month             │
    └────────────────────────────────────────────────┘

With Reserved Instances (1-year):
    ┌────────────────────────────────────────────────┐
    │ Save 40%:            ~$16.50/month             │ ⬇️ 40% OFF
    └────────────────────────────────────────────────┘
```

---

## Quick Command Reference

```bash
# SSH into EC2
ssh -i nijam-key.pem ubuntu@EC2_IP

# Check service status
sudo systemctl status nijam

# View logs
sudo journalctl -u nijam -f

# Restart service
sudo systemctl restart nijam

# Check memory
free -h

# Check disk space
df -h

# Test API
curl http://localhost:8000/health

# Database connection
psql $DATABASE_URL

# Update code
cd ~/nijam && git pull

# Restart after update
sudo systemctl restart nijam
```

---

**Total Deployment Time**: ~60 minutes  
**Difficulty**: ⭐⭐⭐ (Moderate)  
**Success Rate**: 🟢 High (with guide)
