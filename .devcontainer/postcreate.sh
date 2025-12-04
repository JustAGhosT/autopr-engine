#!/bin/bash

# AutoPR Engine DevContainer Post-Create Setup
echo "🚀 Setting up AutoPR Engine development environment..."

# Update package lists
sudo apt-get update

# Install additional development tools
sudo apt-get install -y \
    curl \
    wget \
    jq \
    tree \
    htop \
    vim \
    nano \
    zip \
    unzip \
    build-essential \
    libpq-dev

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
mkdir -p logs
data
temp
.coverage

# Set up environment file from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env 2>/dev/null || echo "# AutoPR Engine Environment Variables" > .env
fi

# Initialize database schema
echo "🗄️ Setting up database schema..."
# Wait for postgres (placeholder)
# e.g., wait-for-it or custom wait loop here
# Initialize schema (placeholder)
# e.g., python scripts/init_db.py or similar
