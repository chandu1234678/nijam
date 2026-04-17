# AWS Free Tier Deployment Guide - Nijam Fact Checker

## 🎯 Overview
Deploy your fact-checking system to AWS Free Tier using EC2 t2.micro (1GB RAM, 1 vCPU).

## 📋 AWS Free Tier Limits
- **EC2**: 750 hours/month of t2.micro (1 vCPU, 1GB RAM)
- **RDS**: 750 hours/month of db.t2.micro (PostgreSQL)
- **S3**: 5GB storage
- **Data Transfer**: 15GB/month outbound
- **Elastic IP**: 1 free (when attached to running instance)

## 🚀 Deployment Options

### Option 1: EC2 + RDS (Recommended)
**Best for**: Production-ready setup with managed database

#### Step 1: Launch EC2 Instance
```bash
# Instance Configuration:
- AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
- Instance Type: t2.micro (1 vCPU, 1GB RAM)
- Storage: 30GB gp2 (Free tier: up to 30GB)
- Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)
```

#### Step 2: Setup RDS PostgreSQL
```bash
# RDS Configuration:
- Engine: PostgreSQL 15
- Instance: db.t2.micro (1 vCPU, 1GB RAM)
- Storage: 20GB gp2 (Free tier: up to 20GB)
- Public Access: No (connect via VPC)
- Security Group: Allow port 5432 from EC2 security group
```

#### Step 3: Connect to EC2 and Setup
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx

# Install PostgreSQL client
sudo apt install -y postgresql-client

# Clone repository
git clone https://github.com/chandu1234678/nijam.git
cd nijam/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

#### Step 4: Configure Environment Variables
```bash
# Copy this to your .env file on EC2:

# API Keys (use your existing keys)
CEREBRAS_API_KEY=csk-6kx2r8xhw9f89nrx9we8mxjk6fvctt6n5vnrxw525kmx3vxh
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=AIzaSyAh5s_OVv45GTzKZ8KJEftylf16MJAg5Gs
NEWS_API_KEY=c5f04780e5f34fb8a6717b3c94997b70
TAVILY_API_KEY=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
SERPAPI_KEY=11e01b51e29c75ae67d2467a047bb771ddcc9885e61677a34535057c6c2c1947
GOOGLE_FACTCHECK_API_KEY=AIzaSyAC1W6wdq29AoPs-Xpv7ykYnKEdewauF1s

# Database (use your RDS endpoint)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@your-rds-endpoint.rds.amazonaws.com:5432/nijam_db

# Security
JWT_SECRET=GENERATE_NEW_SECRET_HERE_USE_openssl_rand_hex_32

# Email (Brevo)
SMTP_USER=factcheckai2@gmail.com
BREVO_API_KEY=your-brevo-api-key

# Google OAuth
GOOGLE_CLIENT_ID=595122585703-1geqe1e5uqd0lt4emf95kel6hsa3r64c.apps.googleusercontent.com

# HuggingFace (for future model downloads)
HF_TOKEN=your-hf-token

# Model Configuration - OPTIMIZED FOR FREE TIER
# Use TF-IDF only (96.63% accuracy, <50MB RAM, instant loading)
DEBERTA_MODEL=
FORCE_TRANSFORMER_LOAD=false
ENABLE_ENSEMBLE=false

# Redis (optional - skip on free tier to save RAM)
# REDIS_URL=redis://localhost:6379
```

#### Step 5: Initialize Database
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Run migrations
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

#### Step 6: Setup Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/nijam.service
```

```ini
[Unit]
Description=Nijam Fact Checker API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nijam/backend
Environment="PATH=/home/ubuntu/nijam/backend/venv/bin"
ExecStart=/home/ubuntu/nijam/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nijam
sudo systemctl start nijam
sudo systemctl status nijam

# View logs
sudo journalctl -u nijam -f
```

#### Step 7: Setup Nginx Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/nijam
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or use EC2 public IP

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/nijam /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 8: Setup SSL with Let's Encrypt (Optional but Recommended)
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

---

### Option 2: AWS Elastic Beanstalk (Easier but Less Control)
**Best for**: Quick deployment with auto-scaling

#### Step 1: Install EB CLI
```bash
pip install awsebcli
```

#### Step 2: Initialize Elastic Beanstalk
```bash
cd nijam/backend
eb init -p python-3.11 nijam-api --region us-east-1
```

#### Step 3: Create Environment
```bash
# Create environment with RDS
eb create nijam-prod \
  --database.engine postgres \
  --database.instance db.t2.micro \
  --instance-type t2.micro \
  --envvars $(cat .env | tr '\n' ',')
```

#### Step 4: Deploy
```bash
eb deploy
eb open
```

---

### Option 3: AWS Lambda + API Gateway (Serverless)
**Best for**: Pay-per-use, auto-scaling, no server management

#### Benefits:
- **Free Tier**: 1M requests/month + 400,000 GB-seconds compute
- **No server maintenance**
- **Auto-scaling**
- **Pay only for actual usage**

#### Limitations:
- Cold start latency (~1-3 seconds)
- 15-minute timeout limit
- More complex setup

#### Setup with Mangum (FastAPI → Lambda adapter):
```bash
# Install Mangum
pip install mangum

# Update main.py
from mangum import Mangum
handler = Mangum(app)

# Deploy with Serverless Framework or AWS SAM
```

---

## 🔧 Free Tier Optimizations

### 1. Memory Optimization
```python
# backend/.env
DEBERTA_MODEL=                    # Empty = use TF-IDF only
FORCE_TRANSFORMER_LOAD=false      # Don't load transformers
ENABLE_ENSEMBLE=false             # Single model only
```

### 2. Database Connection Pooling
```python
# backend/database.py - already optimized
pool_size=5          # Max 5 connections
max_overflow=10      # Allow 10 extra during spikes
pool_pre_ping=True   # Check connection health
```

### 3. Reduce Workers
```bash
# Use 1 worker on t2.micro (1GB RAM)
uvicorn app.main:app --workers 1
```

### 4. Enable Swap (if needed)
```bash
# Add 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 5. Monitoring RAM Usage
```bash
# Check memory
free -h

# Monitor in real-time
watch -n 1 free -h

# Check process memory
ps aux --sort=-%mem | head -10
```

---

## 📊 Performance Benchmarks (t2.micro)

| Configuration | RAM Usage | Response Time | Accuracy |
|--------------|-----------|---------------|----------|
| TF-IDF only | ~200 MB | 50-100ms | 96.63% |
| + Sentence Transformers | ~400 MB | 100-200ms | 96.63% |
| + DeBERTa (268MB) | ~800 MB | 500-1000ms | 97.5% |
| + DeBERTa (738MB) | **OOM** | N/A | N/A |

**Recommendation**: Use TF-IDF only on free tier for best performance.

---

## 🔒 Security Checklist

- [ ] Change JWT_SECRET to a new random value
- [ ] Use RDS with private subnet (no public access)
- [ ] Enable AWS Security Groups (firewall)
- [ ] Setup SSL/TLS with Let's Encrypt
- [ ] Enable CloudWatch logging
- [ ] Setup AWS IAM roles (least privilege)
- [ ] Enable AWS WAF for DDoS protection (optional)
- [ ] Rotate API keys regularly
- [ ] Enable database backups (RDS automated backups)
- [ ] Setup CloudWatch alarms for high CPU/memory

---

## 📈 Monitoring & Logging

### CloudWatch Metrics
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure metrics
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### Application Logs
```bash
# View API logs
sudo journalctl -u nijam -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 💰 Cost Estimation

### Free Tier (First 12 months):
- **EC2 t2.micro**: $0/month (750 hours free)
- **RDS db.t2.micro**: $0/month (750 hours free)
- **Storage**: $0/month (30GB EBS + 20GB RDS free)
- **Data Transfer**: $0/month (15GB free)
- **Total**: **$0/month** ✅

### After Free Tier:
- **EC2 t2.micro**: ~$8.50/month
- **RDS db.t2.micro**: ~$15/month
- **Storage**: ~$3/month
- **Data Transfer**: ~$1/month
- **Total**: ~$27.50/month

### Cost Optimization Tips:
1. Use **Reserved Instances** (save 40-60%)
2. Use **Spot Instances** for non-critical workloads (save 70-90%)
3. Enable **Auto Scaling** to scale down during low traffic
4. Use **S3** for static files instead of EBS
5. Use **CloudFront CDN** (free tier: 50GB/month)

---

## 🚀 Quick Start Commands

```bash
# 1. Launch EC2 instance (via AWS Console)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Run setup script
curl -o setup.sh https://raw.githubusercontent.com/chandu1234678/nijam/main/aws_setup.sh
chmod +x setup.sh
./setup.sh

# 4. Configure environment
cd nijam/backend
nano .env  # Add your API keys and RDS endpoint

# 5. Start service
sudo systemctl start nijam
sudo systemctl status nijam

# 6. Test API
curl http://localhost:8000/health

# 7. Setup Nginx
sudo systemctl start nginx
curl http://your-ec2-ip/health
```

---

## 🐛 Troubleshooting

### Issue: Out of Memory (OOM)
```bash
# Check memory
free -h

# Solution: Add swap or reduce workers
sudo fallocate -l 2G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Database Connection Failed
```bash
# Check RDS security group allows EC2 IP
# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Issue: API Not Responding
```bash
# Check service status
sudo systemctl status nijam

# Check logs
sudo journalctl -u nijam -n 50

# Restart service
sudo systemctl restart nijam
```

### Issue: High CPU Usage
```bash
# Check processes
top

# Reduce workers or enable caching
# Edit .env: ENABLE_CACHE=true
```

---

## 📚 Additional Resources

- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [RDS Pricing](https://aws.amazon.com/rds/postgresql/pricing/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## 🎉 Next Steps

1. **Deploy to AWS** using this guide
2. **Update extension config.js** with your EC2/domain URL
3. **Test all features** end-to-end
4. **Monitor performance** with CloudWatch
5. **Setup CI/CD** with GitHub Actions (optional)
6. **Add custom domain** with Route 53 (optional)

---

**Need Help?** Contact the team:
- Chandu: bc833498@gmail.com
- Kaushik: kaushikram51@gmail.com
- Abhinav: sb346@gmail.com
