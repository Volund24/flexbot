#!/bin/bash

# Configuration
SERVER_IP="172.235.53.198"
SERVER_USER="root"
APP_DIR="/root/flexbot"
REPO_URL="https://github.com/Volund24/flexbot.git"

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Deployment to $SERVER_IP...${NC}"

# 1. SSH into server to setup directories and install dependencies
echo -e "${GREEN}🔧 Checking dependencies on server...${NC}"
ssh $SERVER_USER@$SERVER_IP << EOF
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
scp .env $SERVER_USER@$SERVER_IP:$APP_DIR/.env

# 3. SSH to pull code and restart
echo -e "${GREEN}🔄 Pulling code and restarting container...${NC}"
ssh $SERVER_USER@$SERVER_IP << EOF
    cd $APP_DIR

    if [ -d ".git" ]; then
        echo "Pulling latest changes..."
        git pull
    else
        echo "Cloning repository..."
        git clone $REPO_URL .
    fi

    echo "Building and starting Docker container..."
    docker compose up -d --build --remove-orphans

    echo "✅ Deployment Complete!"
    docker compose ps
EOF
