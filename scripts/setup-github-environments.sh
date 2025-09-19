#!/bin/bash

# GitHub Environment Setup Script
# Creates staging and production environments with protection rules

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
REPO=""
TOKEN=""
DRY_RUN=false

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 -r <repository> -t <token> [options]"
    echo ""
    echo "Options:"
    echo "  -r, --repo     GitHub repository in format 'owner/repo'"
    echo "  -t, --token    GitHub personal access token"
    echo "  -d, --dry-run  Show what would be created without creating"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -r your-org/autopr-engine -t ghp_xxx"
    echo "  $0 -r your-org/autopr-engine -t ghp_xxx --dry-run"
}

# Function to check if GitHub CLI is available
check_github_cli() {
    if command -v gh &> /dev/null; then
        print_color $GREEN "✅ GitHub CLI detected"
        return 0
    else
        print_color $YELLOW "⚠️  GitHub CLI not found. Using REST API directly."
        return 1
    fi
}

# Function to create GitHub environment
create_environment() {
    local repo=$1
    local env_name=$2
    local token=$3
    local dry_run=$4
    
    local base_url="https://api.github.com/repos/$repo/environments"
    local headers=(
        -H "Authorization: Bearer $token"
        -H "Accept: application/vnd.github.v3+json"
        -H "User-Agent: AutoPR-Environment-Setup"
    )
    
    # Create environment configuration based on type
    local config
    case $env_name in
        "staging")
            config='{
                "name": "staging",
                "protection_rules": [
                    {
                        "type": "wait_timer",
                        "wait_timer": 0
                    },
                    {
                        "type": "required_reviewers",
                        "required_reviewers": {
                            "users": [],
                            "teams": []
                        }
                    }
                ],
                "deployment_branch_policy": {
                    "protected_branches": true,
                    "custom_branch_policies": false
                }
            }'
            print_color $CYAN "  📋 Staging: Manual workflow dispatch required"
            ;;
        "production")
            config='{
                "name": "production",
                "protection_rules": [
                    {
                        "type": "wait_timer",
                        "wait_timer": 300
                    },
                    {
                        "type": "required_reviewers",
                        "required_reviewers": {
                            "users": [],
                            "teams": []
                        }
                    }
                ],
                "deployment_branch_policy": {
                    "protected_branches": true,
                    "custom_branch_policies": false
                }
            }'
            print_color $YELLOW "  🚀 Production: Requires approval + 5min wait"
            ;;
    esac
    
    if [ "$dry_run" = true ]; then
        print_color $CYAN "  [DRY RUN] Would create environment: $env_name"
        print_color $CYAN "  [DRY RUN] Configuration: $config"
        return 0
    fi
    
    # Make API call to create environment
    local response
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "${headers[@]}" \
        -X POST "$base_url" \
        -d "$config" \
        -H "Content-Type: application/json")
    
    local http_code="${response: -3}"
    
    case $http_code in
        201)
            print_color $GREEN "  ✅ Created environment: $env_name"
            if command -v jq &> /dev/null; then
                local url=$(jq -r '.html_url' /tmp/response.json)
                print_color $CYAN "  🔗 URL: $url"
            fi
            ;;
        422)
            print_color $YELLOW "  ⚠️  Environment '$env_name' already exists"
            ;;
        *)
            print_color $RED "  ❌ Failed to create environment '$env_name' (HTTP $http_code)"
            if [ -f /tmp/response.json ]; then
                print_color $RED "  Error: $(cat /tmp/response.json)"
            fi
            return 1
            ;;
    esac
    
    # Clean up temp file
    rm -f /tmp/response.json
    return 0
}

# Function to set environment variables
set_environment_variables() {
    local repo=$1
    local env_name=$2
    local token=$3
    local dry_run=$4
    
    local base_url="https://api.github.com/repos/$repo/environments/$env_name/secrets"
    local headers=(
        -H "Authorization: Bearer $token"
        -H "Accept: application/vnd.github.v3+json"
        -H "User-Agent: AutoPR-Environment-Setup"
    )
    
    # Set environment-specific variables
    local node_env
    local log_level
    
    case $env_name in
        "staging")
            node_env="staging"
            log_level="debug"
            ;;
        "production")
            node_env="production"
            log_level="info"
            ;;
    esac
    
    local variables=(
        "DEPLOYMENT_ENV:$env_name"
        "NODE_ENV:$node_env"
        "LOG_LEVEL:$log_level"
    )
    
    print_color $CYAN "  📝 Setting environment variables..."
    
    for var in "${variables[@]}"; do
        local key="${var%%:*}"
        local value="${var##*:}"
        
        if [ "$dry_run" = true ]; then
            print_color $CYAN "  [DRY RUN] Would set variable: $key = $value"
        else
            local var_config="{\"name\": \"$key\", \"value\": \"$value\"}"
            
            local response
            response=$(curl -s -w "%{http_code}" -o /tmp/var_response.json "${headers[@]}" \
                -X POST "$base_url" \
                -d "$var_config" \
                -H "Content-Type: application/json")
            
            local http_code="${response: -3}"
            
            case $http_code in
                201|204)
                    print_color $GREEN "  ✅ Set variable: $key"
                    ;;
                *)
                    print_color $RED "  ❌ Failed to set variable '$key' (HTTP $http_code)"
                    ;;
            esac
            
            rm -f /tmp/var_response.json
        fi
    done
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_color $RED "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$REPO" ] || [ -z "$TOKEN" ]; then
    print_color $RED "❌ Repository and token are required"
    show_usage
    exit 1
fi

# Validate repository format
if [[ ! "$REPO" =~ ^[^/]+/[^/]+$ ]]; then
    print_color $RED "❌ Invalid repository format. Use 'owner/repo' format."
    exit 1
fi

# Main execution
print_color $CYAN "🚀 GitHub Environment Setup Script"
print_color $CYAN "================================="
print_color $CYAN "Repository: $REPO"
print_color $CYAN "Dry Run: $DRY_RUN"
echo ""

# Check GitHub CLI
check_github_cli

echo ""
print_color $CYAN "📋 Creating Environments:"

# Create environments
environments=("staging" "production")
success_count=0

for env in "${environments[@]}"; do
    echo ""
    print_color $CYAN "🔧 Setting up environment: $env"
    
    if create_environment "$REPO" "$env" "$TOKEN" "$DRY_RUN"; then
        ((success_count++))
        set_environment_variables "$REPO" "$env" "$TOKEN" "$DRY_RUN"
    fi
done

echo ""
print_color $CYAN "📊 Summary:"
print_color $CYAN "  Environments processed: ${#environments[@]}"
print_color $GREEN "  Successfully created/verified: $success_count"

if [ $success_count -eq ${#environments[@]} ]; then
    echo ""
    print_color $GREEN "🎉 All environments ready!"
    echo ""
    print_color $CYAN "Next steps:"
    print_color $CYAN "  1. Review environment settings in GitHub repository"
    print_color $CYAN "  2. Add required reviewers if needed"
    print_color $CYAN "  3. Configure deployment secrets (API keys, etc.)"
    print_color $CYAN "  4. Test your CI/CD pipeline"
else
    echo ""
    print_color $YELLOW "⚠️  Some environments failed to create. Check the errors above."
    exit 1
fi
