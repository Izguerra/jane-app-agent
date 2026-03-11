#!/bin/bash

# --- SupaAgent Deployment Script ---

echo "🚀 Starting deployment..."

# 1. Pull latest code from GitHub
echo "📥 Pulling latest changes from GitHub (dev branch)..."
git pull origin dev

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  WARNING: .env file not found! Please create it before running containers."
    exit 1
fi

# 3. Build and restart containers in detached mode
echo "📦 Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# 4. Cleanup
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo "✅ Deployment complete! Backend should be running at http://147.182.149.234:8000"
echo "👉 Check logs with: docker compose -f docker-compose.prod.yml logs -f"
