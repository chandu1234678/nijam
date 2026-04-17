#!/bin/bash
# AWS EC2 Setup Script for Nijam Fact Checker
# Run this on a fresh Ubuntu 22.04 t2.micro instance

set -e  # Exit on error

echo "🚀 Starting Nijam Fact Checker setup on AWS EC2..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo -e "${GREEN}🐍 Installing Python 3.11...${NC}"
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
echo -e "${GREEN}📚 Installing system dependencies...${NC}"
sudo apt install -y git nginx postgresql-client build-essential libpq-dev

# Clone repository
echo -e "${GREEN}📥 Cloning repository...${NC}"
cd ~
if [ -d "nijam" ]; then
    echo -e "${YELLOW}Repository already exists, pulling latest changes...${NC}"
    cd nijam
    git pull
else
    git clone https://github.com/chandu1234678/nijam.git
    cd nijam
fi

# Setup backend
echo -e "${GREEN}⚙️  Setting up backend...${NC}"
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << 'EOF'
# API Keys
CEREBRAS_API_KEY=your_cerebras_key_here
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_news_api_key_here
TAVILY_API_KEY=your_tavily_key_here
SERPAPI_KEY=your_serpapi_key_here
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key_here

# Database (replace with your RDS endpoint)
DATABASE_URL=postgresql://postgres:password@your-rds-endpoint.rds.amazonaws.com:5432/nijam_db

# Security (CHANGE THIS!)
JWT_SECRET=CHANGE_THIS_TO_RANDOM_SECRET

# Email
SMTP_USER=factcheckai2@gmail.com
BREVO_API_KEY=your_brevo_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here

# HuggingFace
HF_TOKEN=your_hf_token_here

# Model Configuration - OPTIMIZED FOR FREE TIER
DEBERTA_MODEL=
FORCE_TRANSFORMER_LOAD=false
ENABLE_ENSEMBLE=false
EOF
    echo -e "${RED}⚠️  IMPORTANT: Edit .env file with your actual API keys!${NC}"
    echo -e "${YELLOW}Run: nano ~/nijam/backend/.env${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Setup systemd service
echo -e "${GREEN}🔧 Setting up systemd service...${NC}"
sudo tee /etc/systemd/system/nijam.service > /dev/null << EOF
[Unit]
Description=Nijam Fact Checker API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/nijam/backend
Environment="PATH=$HOME/nijam/backend/venv/bin"
ExecStart=$HOME/nijam/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx
echo -e "${GREEN}🌐 Setting up Nginx...${NC}"
sudo tee /etc/nginx/sites-available/nijam > /dev/null << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name _;

    # Max body size for image uploads
    client_max_body_size 10M;

    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
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

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/nijam /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Setup swap (important for t2.micro with 1GB RAM)
echo -e "${GREEN}💾 Setting up swap space (2GB)...${NC}"
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo -e "${GREEN}✓ Swap enabled${NC}"
else
    echo -e "${YELLOW}Swap already exists${NC}"
fi

# Enable services
echo -e "${GREEN}🚀 Enabling services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable nijam
sudo systemctl enable nginx

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your API keys:"
echo "   nano ~/nijam/backend/.env"
echo ""
echo "2. Run database migrations:"
echo "   cd ~/nijam/backend"
echo "   source venv/bin/activate"
echo "   alembic upgrade head"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start nijam"
echo "   sudo systemctl start nginx"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status nijam"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u nijam -f"
echo ""
echo -e "${GREEN}🎉 Your API will be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)${NC}"
