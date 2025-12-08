#!/bin/bash
# AutoPR Engine - Simple Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | bash
# Or: ./install.sh [--full|--dev|--minimal]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with color
print_status() { echo -e "${BLUE}[*]${NC} $1"; }
print_success() { echo -e "${GREEN}[+]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[-]${NC} $1"; }

# Banner
echo ""
echo "  ___        _        ____  ____    _____             _            "
echo " / _ \      | |      |  _ \|  _ \  | ____|_ __   __ _(_)_ __   ___ "
echo "| |_| |_   _| |_ ___ | |_) | |_) | |  _| | '_ \ / _\` | | '_ \ / _ \\"
echo "|  _  | | | | __/ _ \|  __/|  _ <  | |___| | | | (_| | | | | |  __/"
echo "|_| |_|\__,_|\__\___/|_|   |_| \_\ |_____|_| |_|\__, |_|_| |_|\___|"
echo "                                                |___/              "
echo ""
echo "AI-Powered GitHub PR Automation and Issue Management"
echo ""

# Version
VERSION="1.0.0"

# Detect installation type
INSTALL_TYPE="standard"
if [ "$1" = "--full" ]; then
    INSTALL_TYPE="full"
elif [ "$1" = "--dev" ]; then
    INSTALL_TYPE="dev"
elif [ "$1" = "--minimal" ]; then
    INSTALL_TYPE="minimal"
elif [ "$1" = "--docker" ]; then
    INSTALL_TYPE="docker"
elif [ "$1" = "--action" ]; then
    INSTALL_TYPE="action"
elif [ "$1" = "--version" ] || [ "$1" = "-v" ]; then
    echo "AutoPR Engine Installer v${VERSION}"
    exit 0
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    # Show banner in help output
    echo ""
    echo "  ___        _        ____  ____    _____             _            "
    echo " / _ \      | |      |  _ \|  _ \  | ____|_ __   __ _(_)_ __   ___ "
    echo "| |_| |_   _| |_ ___ | |_) | |_) | |  _| | '_ \ / _\` | | '_ \ / _ \\"
    echo "|  _  | | | | __/ _ \|  __/|  _ <  | |___| | | | (_| | | | | |  __/"
    echo "|_| |_|\__,_|\__\___/|_|   |_| \_\ |_____|_| |_|\__, |_|_| |_|\___|"
    echo "                                                |___/              "
    echo ""
    echo "AutoPR - AI-Powered GitHub PR Automation and Issue Management"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --minimal   Install core package only (no extras)"
    echo "  --standard  Install with common features (default)"
    echo "  --full      Install with all features and integrations"
    echo "  --dev       Install for development (includes dev tools)"
    echo "  --docker    Set up Docker-based installation"
    echo "  --action    Set up GitHub Action workflow in current repo"
    echo "  --version   Show installer version"
    echo "  --help      Show this help message"
    echo ""
    exit 0
fi

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

        # Check for Python 3.12+ (or Python 4+)
        if [ "$PYTHON_MAJOR" -gt 3 ]; then
            print_success "Python $PYTHON_VERSION detected"
        elif [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
            print_success "Python $PYTHON_VERSION detected"
        else
            print_error "Python 3.12+ required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.12+"
        exit 1
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install pip"
        exit 1
    fi
    print_success "pip detected"

    # Check Docker for docker install type
    if [ "$INSTALL_TYPE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker not found. Please install Docker"
            exit 1
        fi
        print_success "Docker detected"

        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            print_success "Docker Compose detected"
        else
            print_warning "Docker Compose not found. Some features may be limited"
        fi
    fi
}

# Install via pip
install_pip() {
    print_status "Installing AutoPR Engine via pip..."

    # Recommend virtual environment
    if [ -z "$VIRTUAL_ENV" ] && [ "$INSTALL_TYPE" != "minimal" ]; then
        print_warning "Consider using a virtual environment: python3 -m venv venv && source venv/bin/activate"
    fi

    case "$INSTALL_TYPE" in
        "minimal")
            print_status "Installing minimal package (core only, no extras)..."
            pip3 install --no-deps autopr-engine || {
                print_error "Installation failed"
                exit 1
            }
            ;;
        "standard")
            print_status "Installing standard package with common dependencies..."
            pip3 install autopr-engine || {
                print_error "Installation failed"
                exit 1
            }
            ;;
        "full")
            print_status "Installing full package with all features..."
            pip3 install "codeflow-engine[full]" || {
                print_error "Installation failed"
                exit 1
            }
            ;;
        "dev")
            print_status "Installing development package..."
            if [ -f "pyproject.toml" ]; then
                # We're in the repo
                pip3 install -e ".[dev]" || {
                    print_error "Installation failed"
                    exit 1
                }
            else
                # Clone and install
                print_status "Cloning repository..."
                CLONE_DIR=$(mktemp -d)
                if git clone https://github.com/JustAGhosT/codeflow-engine.git "${CLONE_DIR}/codeflow-engine"; then
                    cd "${CLONE_DIR}/codeflow-engine"
                    pip3 install -e ".[dev]" || {
                        print_error "Installation failed"
                        rm -rf "${CLONE_DIR}"
                        exit 1
                    }
                    print_status "Repository cloned to: ${CLONE_DIR}/autopr-engine"
                else
                    print_error "Failed to clone repository"
                    rm -rf "${CLONE_DIR}"
                    exit 1
                fi
            fi
            ;;
    esac

    print_success "AutoPR Engine installed successfully!"
}

# Install via Docker
install_docker() {
    print_status "Setting up Docker installation..."

    # Create directory if not in repo
    if [ ! -f "docker-compose.yml" ]; then
        print_status "Creating autopr directory..."
        mkdir -p codeflow-engine && cd codeflow-engine || {
            print_error "Failed to create directory"
            exit 1
        }

        # Download docker-compose.yml with retry
        print_status "Downloading Docker Compose configuration..."
        for i in 1 2 3; do
            if curl -sSL --fail https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/docker-compose.yml -o docker-compose.yml; then
                break
            fi
            if [ "$i" -eq 3 ]; then
                print_error "Failed to download docker-compose.yml after 3 attempts"
                exit 1
            fi
            print_warning "Download failed, retrying... ($i/3)"
            sleep 2
        done

        for i in 1 2 3; do
            if curl -sSL --fail https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/.env.example -o .env.example; then
                break
            fi
            if [ "$i" -eq 3 ]; then
                print_error "Failed to download .env.example after 3 attempts"
                exit 1
            fi
            print_warning "Download failed, retrying... ($i/3)"
            sleep 2
        done
    fi

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your API keys before starting"
    fi

    print_success "Docker setup complete!"
    echo ""
    print_status "To start AutoPR Engine:"
    echo "  1. Edit .env with your API keys"
    echo "  2. Run: docker compose up -d"
}

# Create environment file
setup_env() {
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        print_status "Creating .env from template..."
        cp .env.example .env
        print_warning "Remember to edit .env with your API keys!"
    fi
}

# Post-install instructions
show_next_steps() {
    echo ""
    echo "=========================================="
    print_success "Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Set up your API keys:"
    echo "     export GITHUB_TOKEN=ghp_your_token"
    echo "     export OPENAI_API_KEY=sk-your_key"
    echo ""
    echo "  2. Run AutoPR CLI:"
    echo "     autopr --help"
    echo ""
    echo "  3. Add to your GitHub repo:"
    echo "     autopr init  # Creates .github/workflows/autopr.yml"
    echo ""
    echo "  4. Or use Docker:"
    echo "     docker-compose up -d"
    echo ""
    echo "Documentation: https://github.com/JustAGhosT/codeflow-engine"
    echo ""
}

# GitHub Action setup helper
setup_github_action() {
    print_status "Setting up GitHub Action workflow..."

    mkdir -p .github/workflows

    cat > .github/workflows/autopr.yml << 'EOF'
# AutoPR Engine - AI-Powered PR Analysis
# Generated by install.sh
name: AutoPR Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install AutoPR Engine
        run: pip install autopr-engine

      - name: Run PR Analysis
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          autopr analyze \
            --repo ${{ github.repository }} \
            --pr ${{ github.event.pull_request.number }}
EOF

    print_success "Created .github/workflows/autopr.yml"
    print_warning "Remember to add OPENAI_API_KEY to your repository secrets!"
}

# Main installation flow
main() {
    case "$INSTALL_TYPE" in
        "action")
            setup_github_action
            ;;
        "docker")
            check_prerequisites
            install_docker
            ;;
        *)
            check_prerequisites
            install_pip
            setup_env
            show_next_steps
            ;;
    esac
}

# Run main
main
