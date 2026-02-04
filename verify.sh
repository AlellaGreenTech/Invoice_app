#!/bin/bash

# Invoice Processor - Verification Script
# This script verifies that all components are properly set up

set -e

echo "🔍 Invoice Processor - System Verification"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    docker --version
else
    check_fail "Docker is not installed"
    exit 1
fi

echo ""

# Check Docker Compose
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed"
    docker-compose --version
else
    check_fail "Docker Compose is not installed"
    exit 1
fi

echo ""

# Check .env file
echo "Checking environment configuration..."
if [ -f .env ]; then
    check_pass ".env file exists"

    # Check for placeholder values
    if grep -q "your-client-id" .env; then
        check_warn "GOOGLE_CLIENT_ID contains placeholder value"
    else
        check_pass "GOOGLE_CLIENT_ID is configured"
    fi

    if grep -q "your-client-secret" .env; then
        check_warn "GOOGLE_CLIENT_SECRET contains placeholder value"
    else
        check_pass "GOOGLE_CLIENT_SECRET is configured"
    fi

    if grep -q "your-anthropic-api-key" .env; then
        check_warn "ANTHROPIC_API_KEY contains placeholder value"
    else
        check_pass "ANTHROPIC_API_KEY is configured"
    fi
else
    check_fail ".env file not found"
    echo "   Run: cp .env.example .env"
    exit 1
fi

echo ""

# Check project structure
echo "Checking project structure..."
required_dirs=("app" "app/auth" "app/invoices" "app/exports" "app/templates" "app/static" "tests")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Directory exists: $dir"
    else
        check_fail "Directory missing: $dir"
    fi
done

echo ""

# Check key files
echo "Checking key files..."
required_files=(
    "run.py"
    "celery_worker.py"
    "requirements.txt"
    "docker-compose.yml"
    "Dockerfile"
    "app/__init__.py"
    "app/models.py"
    "app/config.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File exists: $file"
    else
        check_fail "File missing: $file"
    fi
done

echo ""

# Check if services are running
echo "Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    check_pass "Docker services are running"
    docker-compose ps
else
    check_warn "Docker services are not running"
    echo "   Run: docker-compose up -d"
fi

echo ""

# Count files
echo "Project Statistics:"
py_files=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | wc -l)
html_files=$(find . -name "*.html" | wc -l)
test_files=$(find ./tests -name "test_*.py" 2>/dev/null | wc -l)
doc_files=$(find . -maxdepth 1 -name "*.md" | wc -l)

echo "  Python files: $py_files"
echo "  HTML templates: $html_files"
echo "  Test files: $test_files"
echo "  Documentation files: $doc_files"

echo ""

# Check Python dependencies
echo "Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    dep_count=$(wc -l < requirements.txt)
    check_pass "requirements.txt has $dep_count dependencies"
else
    check_fail "requirements.txt not found"
fi

echo ""

# Final summary
echo "=========================================="
echo "Verification Summary:"
echo ""

if grep -q "your-client-id\|your-client-secret\|your-anthropic-api-key" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠ Action Required:${NC}"
    echo "  1. Update .env with your API credentials"
    echo "  2. Get Google OAuth credentials from: https://console.cloud.google.com/"
    echo "  3. Get Anthropic API key from: https://console.anthropic.com/"
    echo ""
fi

if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠ Next Steps:${NC}"
    echo "  1. Start services: docker-compose up -d"
    echo "  2. Run migrations: docker-compose exec web flask db upgrade"
    echo "  3. Seed categories: docker-compose exec web flask seed-categories"
    echo "  4. Access app: http://localhost:5000"
else
    echo -e "${GREEN}✓ System Ready!${NC}"
    echo "  Access the application at: http://localhost:5000"
fi

echo ""
echo "For detailed setup instructions, see: QUICKSTART.md"
echo "For troubleshooting, see: README.md"
echo ""
