#!/bin/bash

# AutoPR Engine DevContainer Post-Start Script
# Runs every time the container starts

echo "==================================="
echo "AutoPR Engine Development Environment"
echo "==================================="
echo ""

# Check if .env has been configured
if grep -q "CHANGE_ME" .env 2>/dev/null || grep -q "your_token" .env 2>/dev/null; then
    echo "⚠️  Warning: .env contains placeholder values"
    echo "   Please update .env with your actual API keys"
    echo ""
fi

# Show quick start info
echo "Quick Commands:"
echo "  make help      - Show all available commands"
echo "  make test      - Run tests"
echo "  make lint      - Run linters"
echo "  make server    - Start API server (port 8080)"
echo ""
echo "Documentation: https://github.com/JustAGhosT/codeflow-engine"
echo ""
