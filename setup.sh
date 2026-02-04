#!/bin/bash

# Invoice Processor - Quick Setup Script
# This script helps you set up the application quickly

set -e

echo "🚀 Invoice Processor - Setup Script"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists and has credentials
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials:"
    echo "   - GOOGLE_CLIENT_ID"
    echo "   - GOOGLE_CLIENT_SECRET"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - SECRET_KEY"
    echo ""
    echo "Run this script again after updating .env"
    exit 1
fi

# Check if credentials are configured
if grep -q "your-client-id" .env || grep -q "your-anthropic-api-key" .env; then
    echo "⚠️  Warning: .env file contains placeholder values"
    echo "   Please update with your actual credentials:"
    echo "   - GOOGLE_CLIENT_ID"
    echo "   - GOOGLE_CLIENT_SECRET"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "✅ Services are running"
echo ""

echo "🗄️  Initializing database..."
docker-compose exec -T web flask db upgrade

echo ""
echo "🌱 Seeding default categories..."
docker-compose exec -T web flask seed-categories

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Application is ready!"
echo "   URL: http://localhost:5000"
echo ""
echo "📝 Next steps:"
echo "   1. Open http://localhost:5000 in your browser"
echo "   2. Click 'Sign in with Google'"
echo "   3. Upload invoices from Google Drive"
echo ""
echo "📚 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Run tests:        docker-compose exec web pytest"
echo "   Access shell:     docker-compose exec web flask shell"
echo ""
echo "🎉 Happy invoice processing!"
