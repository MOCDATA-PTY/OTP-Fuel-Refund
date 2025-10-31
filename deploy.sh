#!/bin/bash

# Simple Redeployment Script for FRI Company
# Just pull new code and restart Gunicorn

set -e

echo "🚀 Starting FRI redeployment..."

# Configuration
PROJECT_DIR="/var/www/OTP-Fuel-Refund"
PROJECT_NAME="fuelrefund"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📁 Navigating to project directory...${NC}"
cd "$PROJECT_DIR"

echo -e "${YELLOW}📥 Pulling latest code from GitHub...${NC}"
git pull origin main || git pull origin master

echo -e "${YELLOW}📦 Installing/updating dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

echo -e "${YELLOW}🔄 Running database migrations...${NC}"
./venv/bin/python manage.py migrate

echo -e "${YELLOW}📦 Collecting static files...${NC}"
./venv/bin/python manage.py collectstatic --noinput

echo -e "${YELLOW}🔄 Killing existing Gunicorn process...${NC}"
sudo supervisorctl stop "$PROJECT_NAME" || pkill -f gunicorn || true

echo -e "${YELLOW}🚀 Starting Gunicorn again...${NC}"
sudo supervisorctl start "$PROJECT_NAME"

echo -e "${YELLOW}🌐 Restarting Nginx...${NC}"
sudo systemctl restart nginx

echo -e "${GREEN}✅ Redeployment completed successfully!${NC}"
echo -e "${GREEN}🎉 FRI is now running the latest code!${NC}"