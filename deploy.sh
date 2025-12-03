#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

# Configuration
SERVER_IP="your_ip"
SERVER_USER="root"
APP_DIR="/root/flexbot"
REPO_URL="https://github.com/Volund24/flexbot.git"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Deployment to $SERVER_IP...${NC}"

# Function to handle errors
handle_error() {
    echo -e "${RED}❌ Error occurred on line $1${NC}"
    exit 1
}
trap 'handle_error $LINENO' ERR

# 1. SSH into server to setup directories and install dependencies
echo -e "${GREEN}🔧 Checking dependencies on server...${NC}"
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
    # Update and install git/docker if missing
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
    fi

    if ! command -v git &> /dev/null; then
        echo "Installing Git..."
        apt-get update && apt-get install -y git
    fi

    # Create app directory
    mkdir -p $APP_DIR
EOF

# 2. Copy local .env to server
echo -e "${GREEN}📦 Copying local .env file to server...${NC}"
scp -o StrictHostKeyChecking=no .env $SERVER_USER@$SERVER_IP:$APP_DIR/.env

# 3. SSH to pull code and restart
echo -e "${GREEN}🔄 Pulling code and restarting container...${NC}"
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
    cd $APP_DIR

    # Check if .git exists, if not, initialize and fetch (works even if folder is not empty)
    if [ ! -d ".git" ]; then
        echo "Initializing repository..."
        git init
        git remote add origin $REPO_URL
        git fetch
        # Force checkout main branch
        git checkout -B main origin/main
    else
        echo "Pulling latest changes..."
        git pull origin main
    fi

    echo "Building and starting Docker container..."
    docker compose up -d --build --remove-orphans

    echo "✅ Deployment Complete! Checking logs..."
    sleep 2
    docker compose logs flexbot --tail=20
EOF
