# AWS Free Tier Deployment Checklist ✅

## Pre-Deployment Checklist

### 1. AWS Account Setup
- [ ] Create AWS account (if not already done)
- [ ] Verify email and add payment method
- [ ] Enable MFA (Multi-Factor Authentication) for security
- [ ] Create IAM user with appropriate permissions (don't use root account)

### 2. Local Testing Complete
- [x] Backend running successfully on localhost:8000
- [x] All 22 stress tests passing ✅
- [x] TF-IDF model loaded (96.63% accuracy)
- [x] Viral detection working
- [x] Anonymous access working
- [x] Rate limiting working
- [x] Authentication working
- [x] Image upload implemented

### 3. Configuration Files Ready
- [ ] `.env` file with all API keys
- [ ] `requirements.txt` up to date
- [ ] `Procfile` configured
- [ ] `runtime.txt` specifies Python 3.11
- [ ] Database migrations ready (`alembic/versions/`)

---

## AWS Setup Steps

### Phase 1: Create RDS Database (15 minutes)

1. **Navigate to RDS Console**
   - Go to AWS Console → RDS → Create database

2. **Database Configuration**
   ```
   Engine: PostgreSQL 15.x
   Template: Free tier
   DB Instance: db.t2.micro
   Storage: 20 GB gp2 (SSD)
   Storage autoscaling: Disabled (to stay in free tier)
   
   DB instance identifier: nijam-db
   Master username: postgres
   Master password: [SAVE THIS SECURELY]
   
   VPC: Default VPC
   Public access: No (more secure)
   VPC security group: Create new → nijam-db-sg
   
   Initial database name: nijam_db
   Backup retention: 7 days (free)
   Encryption: Enabled
   ```

3. **Save Database Endpoint**
   ```
   Example: nijam-db.abc123.us-east-1.rds.amazonaws.com
   ```

4. **Configure Security Group**
   - Edit `nijam-db-sg` security group
   - Add inbound rule: PostgreSQL (5432) from EC2 security group

### Phase 2: Launch EC2 Instance (10 minutes)

1. **Navigate to EC2 Console**
   - Go to AWS Console → EC2 → Launch Instance

2. **Instance Configuration**
   ```
   Name: nijam-api-server
   AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
   Instance type: t2.micro (1 vCPU, 1 GB RAM)
   
   Key pair: Create new → nijam-key.pem [DOWNLOAD AND SAVE]
   
   Network settings:
   - VPC: Same as RDS
   - Auto-assign public IP: Enable
   - Security group: Create new → nijam-api-sg
   
   Storage: 30 GB gp2 (Free tier: up to 30 GB)
   ```

3. **Configure Security Group (nijam-api-sg)**
   ```
   Inbound rules:
   - SSH (22) from My IP (for management)
   - HTTP (80) from Anywhere (0.0.0.0/0)
   - HTTPS (443) from Anywhere (0.0.0.0/0)
   - Custom TCP (8000) from Anywhere (for testing, remove later)
   ```

4. **Launch Instance**
   - Wait for instance state: Running
   - Note public IP address

### Phase 3: Deploy Application (20 minutes)

1. **Connect to EC2**
   ```bash
   # Make key file secure
   chmod 400 nijam-key.pem
   
   # SSH into instance
   ssh -i nijam-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
   ```

2. **Run Setup Script**
   ```bash
   # Download and run setup script
   curl -o setup.sh https://raw.githubusercontent.com/chandu1234678/nijam/main/aws_setup.sh
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure Environment**
   ```bash
   cd ~/nijam/backend
   nano .env
   ```
   
   Update these values:
   ```env
   # Database - use your RDS endpoint
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_RDS_ENDPOINT:5432/nijam_db
   
   # Security - generate new secret
   JWT_SECRET=$(openssl rand -hex 32)
   
   # Add all your API keys from local .env
   ```

4. **Initialize Database**
   ```bash
   source venv/bin/activate
   
   # Test connection
   psql $DATABASE_URL -c "SELECT version();"
   
   # Run migrations
   alembic upgrade head
   
   # Verify
   psql $DATABASE_URL -c "\dt"
   ```

5. **Start Services**
   ```bash
   # Start API
   sudo systemctl start nijam
   sudo systemctl status nijam
   
   # Start Nginx
   sudo systemctl start nginx
   sudo systemctl status nginx
   ```

6. **Test Deployment**
   ```bash
   # Test locally
   curl http://localhost:8000/health
   
   # Test from outside (use EC2 public IP)
   curl http://YOUR_EC2_PUBLIC_IP/health
   ```

### Phase 4: SSL Setup (Optional but Recommended) (10 minutes)

1. **Get Domain Name** (optional)
   - Use Route 53 or external provider (Namecheap, GoDaddy)
   - Point A record to EC2 public IP

2. **Install Certbot**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   ```

3. **Get SSL Certificate**
   ```bash
   # If using domain
   sudo certbot --nginx -d yourdomain.com
   
   # Follow prompts
   # Auto-renewal is configured automatically
   ```

### Phase 5: Update Extension (5 minutes)

1. **Update config.js**
   ```javascript
   // extension/popup/config.js
   const API_BASE_URL = 'http://YOUR_EC2_PUBLIC_IP';
   // or with domain: 'https://yourdomain.com'
   ```

2. **Test Extension**
   - Load extension in Chrome
   - Test fact-checking
   - Test image upload
   - Test viral detection

---

## Post-Deployment Checklist

### Monitoring
- [ ] Setup CloudWatch alarms for high CPU/memory
- [ ] Enable CloudWatch logs
- [ ] Monitor disk space usage
- [ ] Check application logs: `sudo journalctl -u nijam -f`

### Security
- [ ] Remove port 8000 from security group (use Nginx only)
- [ ] Enable AWS WAF (optional, for DDoS protection)
- [ ] Setup automated backups
- [ ] Rotate API keys regularly
- [ ] Review IAM permissions

### Performance
- [ ] Test response times
- [ ] Monitor RAM usage: `free -h`
- [ ] Check swap usage: `swapon --show`
- [ ] Verify rate limiting works
- [ ] Test concurrent load

### Backup
- [ ] Enable RDS automated backups (already enabled)
- [ ] Test database restore procedure
- [ ] Backup .env file securely
- [ ] Document recovery procedures

---

## Verification Tests

Run these tests after deployment:

```bash
# 1. Health check
curl https://yourdomain.com/health

# 2. Fact check test
curl -X POST https://yourdomain.com/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Breaking: Scientists confirm earth is flat"}'

# 3. Viral detection test
curl https://yourdomain.com/velocity/stats

# 4. Stress test (from local machine)
cd backend
python tests/stress_test.py https://yourdomain.com
```

---

## Cost Monitoring

### Free Tier Usage Dashboard
- Go to AWS Console → Billing → Free Tier
- Monitor usage:
  - EC2: 750 hours/month (should be ~100%)
  - RDS: 750 hours/month (should be ~100%)
  - Data transfer: 15 GB/month
  - Storage: 30 GB EBS + 20 GB RDS

### Set Billing Alerts
1. Go to CloudWatch → Alarms → Billing
2. Create alarm: Alert when charges > $1
3. Add email notification

---

## Troubleshooting Guide

### Issue: Can't connect to EC2
```bash
# Check security group allows SSH from your IP
# Verify key file permissions: chmod 400 nijam-key.pem
# Check instance is running in EC2 console
```

### Issue: Database connection failed
```bash
# Check RDS security group allows EC2 security group
# Verify DATABASE_URL in .env
# Test: psql $DATABASE_URL -c "SELECT 1;"
```

### Issue: API not responding
```bash
# Check service status
sudo systemctl status nijam

# View logs
sudo journalctl -u nijam -n 100

# Restart service
sudo systemctl restart nijam
```

### Issue: Out of memory
```bash
# Check memory
free -h

# Check swap
swapon --show

# Add more swap if needed
sudo fallocate -l 4G /swapfile2
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2
sudo swapon /swapfile2
```

### Issue: High CPU usage
```bash
# Check processes
top

# Reduce workers in systemd service
sudo nano /etc/systemd/system/nijam.service
# Change: --workers 1 (already set)

# Restart
sudo systemctl daemon-reload
sudo systemctl restart nijam
```

---

## Maintenance Schedule

### Daily
- [ ] Check application logs for errors
- [ ] Monitor API response times
- [ ] Verify backups completed

### Weekly
- [ ] Review CloudWatch metrics
- [ ] Check disk space usage
- [ ] Update dependencies if needed
- [ ] Review security logs

### Monthly
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Rotate API keys
- [ ] Review AWS costs
- [ ] Test disaster recovery

---

## Emergency Contacts

**Team:**
- Chandu: bc833498@gmail.com
- Kaushik: kaushikram51@gmail.com
- Abhinav: sb346@gmail.com

**AWS Support:**
- Free tier: Community forums
- Paid: AWS Support Center

---

## Success Criteria

✅ **Deployment is successful when:**
1. Health endpoint returns 200 OK
2. Fact-checking works correctly
3. Viral detection tracks claims
4. Image upload processes correctly
5. All 22 stress tests pass
6. Response time < 500ms for simple queries
7. No memory errors in logs
8. SSL certificate valid (if using HTTPS)
9. Extension connects successfully
10. Database migrations applied

---

## Next Steps After Deployment

1. **Monitor for 24 hours** - Watch for any errors or performance issues
2. **Test with real users** - Have team test all features
3. **Setup CI/CD** - Automate deployments with GitHub Actions
4. **Add monitoring** - Setup Grafana dashboard (optional)
5. **Document issues** - Keep track of any problems and solutions
6. **Plan scaling** - If traffic grows, consider upgrading instance

---

**Estimated Total Time: 60-90 minutes**

Good luck with your deployment! 🚀
