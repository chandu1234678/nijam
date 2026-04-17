# ⚡ Quick Deploy to AWS - Nijam Fact Checker

## 🎯 One-Command Deployment

### Prerequisites (5 minutes)
1. AWS account with free tier
2. EC2 key pair downloaded (`nijam-key.pem`)
3. RDS PostgreSQL database created
4. EC2 instance running (Ubuntu 22.04, t2.micro)

### Deploy in 3 Commands

```bash
# 1. SSH into EC2
ssh -i nijam-key.pem ubuntu@YOUR_EC2_IP

# 2. Run setup script
curl -o setup.sh https://raw.githubusercontent.com/chandu1234678/nijam/main/aws_setup.sh && chmod +x setup.sh && ./setup.sh

# 3. Configure and start
cd ~/nijam/backend
nano .env  # Add your API keys and RDS endpoint
source venv/bin/activate
alembic upgrade head
sudo systemctl start nijam nginx
```

### Test Deployment
```bash
curl http://YOUR_EC2_IP/health
```

**Done!** 🎉

---

## 📋 Essential Configuration

### .env File (Minimum Required)
```env
# Database (REQUIRED)
DATABASE_URL=postgresql://postgres:PASSWORD@RDS_ENDPOINT:5432/nijam_db

# Security (REQUIRED - generate new!)
JWT_SECRET=$(openssl rand -hex 32)

# AI APIs (REQUIRED for fact-checking)
CEREBRAS_API_KEY=your_key
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key

# Model (REQUIRED for free tier)
DEBERTA_MODEL=
FORCE_TRANSFORMER_LOAD=false
```

---

## 🚨 Common Issues & Fixes

### Issue: Can't connect to EC2
```bash
# Fix: Check security group allows SSH (port 22) from your IP
chmod 400 nijam-key.pem
```

### Issue: Database connection failed
```bash
# Fix: Check RDS security group allows EC2 security group
# Test: psql $DATABASE_URL -c "SELECT 1;"
```

### Issue: Out of memory
```bash
# Fix: Add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Service won't start
```bash
# Check logs
sudo journalctl -u nijam -n 50

# Restart
sudo systemctl restart nijam
```

---

## 📊 Quick Health Check

```bash
# 1. Service status
sudo systemctl status nijam

# 2. API health
curl http://localhost:8000/health

# 3. Memory usage
free -h

# 4. Logs
sudo journalctl -u nijam -f
```

---

## 🎯 AWS Free Tier Limits

| Resource | Limit | Usage |
|----------|-------|-------|
| EC2 | 750 hrs/month | ~100% |
| RDS | 750 hrs/month | ~100% |
| Storage | 30 GB EBS + 20 GB RDS | ~50 GB |
| Data | 15 GB/month | <5 GB |

**Cost**: $0/month for first 12 months ✅

---

## 🔗 Quick Links

- **Full Guide**: `AWS_DEPLOYMENT_GUIDE.md`
- **Checklist**: `AWS_DEPLOYMENT_CHECKLIST.md`
- **Production Config**: `backend/.env.production`
- **Setup Script**: `aws_setup.sh`

---

## 📞 Need Help?

- **Chandu**: bc833498@gmail.com
- **Kaushik**: kaushikram51@gmail.com
- **Abhinav**: sb346@gmail.com

---

**Deployment Time**: ~60 minutes  
**Status**: ✅ Production Ready
