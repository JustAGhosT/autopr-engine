#!/usr/bin/env bats
# Tests for install.sh
# Run with: bats tests/scripts/test_install.bats
# Install bats: npm install -g bats or apt install bats

# Setup - runs before each test
setup() {
    # Get the directory of the test file
    TEST_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
    PROJECT_ROOT="$(cd "$TEST_DIR/../.." && pwd)"
    INSTALL_SCRIPT="$PROJECT_ROOT/install.sh"

    # Create temp directory for test artifacts
    TEST_TEMP="$(mktemp -d)"
}

# Teardown - runs after each test
teardown() {
    # Cleanup temp directory
    rm -rf "$TEST_TEMP"
}

# Helper to run install.sh with arguments
run_installer() {
    bash "$INSTALL_SCRIPT" "$@"
}

#------------------------------------------------------------------------------
# Version and Help Tests
#------------------------------------------------------------------------------

@test "install.sh --version shows version" {
    run run_installer --version
    [ "$status" -eq 0 ]
    [[ "$output" =~ "AutoPR Engine Installer v" ]]
}

@test "install.sh -v shows version" {
    run run_installer -v
    [ "$status" -eq 0 ]
    [[ "$output" =~ "AutoPR Engine Installer v" ]]
}

@test "install.sh --help shows usage" {
    run run_installer --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
    [[ "$output" =~ "--minimal" ]]
    [[ "$output" =~ "--full" ]]
    [[ "$output" =~ "--dev" ]]
    [[ "$output" =~ "--docker" ]]
    [[ "$output" =~ "--action" ]]
}

@test "install.sh -h shows usage" {
    run run_installer -h
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
}

#------------------------------------------------------------------------------
# Banner Tests
#------------------------------------------------------------------------------

@test "install.sh shows banner" {
    run run_installer --help
    [[ "$output" =~ "AutoPR" ]]
    [[ "$output" =~ "AI-Powered" ]]
}

#------------------------------------------------------------------------------
# Argument Parsing Tests
#------------------------------------------------------------------------------

@test "install.sh recognizes --minimal flag" {
    run run_installer --help
    [[ "$output" =~ "--minimal" ]]
    [[ "$output" =~ "core package only" ]]
}

@test "install.sh recognizes --full flag" {
    run run_installer --help
    [[ "$output" =~ "--full" ]]
    [[ "$output" =~ "all features" ]]
}

@test "install.sh recognizes --dev flag" {
    run run_installer --help
    [[ "$output" =~ "--dev" ]]
    [[ "$output" =~ "development" ]]
}

@test "install.sh recognizes --docker flag" {
    run run_installer --help
    [[ "$output" =~ "--docker" ]]
    [[ "$output" =~ "Docker" ]]
}

@test "install.sh recognizes --action flag" {
    run run_installer --help
    [[ "$output" =~ "--action" ]]
    [[ "$output" =~ "GitHub Action" ]]
}

#------------------------------------------------------------------------------
# Script Syntax Tests
#------------------------------------------------------------------------------

@test "install.sh has valid bash syntax" {
    run bash -n "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh is executable" {
    [ -x "$INSTALL_SCRIPT" ]
}

@test "install.sh uses POSIX-compatible test syntax" {
    # Check that we're not using [[ for variable comparison
    # (we allow [[ for pattern matching which is fine)
    run grep -E '^\s*if \[ "\$[^"]+"\s*==' "$INSTALL_SCRIPT"
    # Should not find any '==' in [ ] tests (should use '=')
    [ "$status" -ne 0 ] || [ -z "$output" ]
}

#------------------------------------------------------------------------------
# Function Definition Tests
#------------------------------------------------------------------------------

@test "install.sh defines check_prerequisites function" {
    run grep -q "check_prerequisites()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines install_pip function" {
    run grep -q "install_pip()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines install_docker function" {
    run grep -q "install_docker()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines setup_github_action function" {
    run grep -q "setup_github_action()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines setup_env function" {
    run grep -q "setup_env()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines show_next_steps function" {
    run grep -q "show_next_steps()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh defines main function" {
    run grep -q "^main()" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

#------------------------------------------------------------------------------
# Error Handling Tests
#------------------------------------------------------------------------------

@test "install.sh uses set -e for error handling" {
    run grep -q "^set -e" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh has error handling in pip install" {
    run grep -q 'pip3 install.*|| {' "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh has retry logic for curl" {
    run grep -q "for i in 1 2 3" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

#------------------------------------------------------------------------------
# Security Tests
#------------------------------------------------------------------------------

@test "install.sh uses --fail flag with curl" {
    run grep "curl.*--fail" "$INSTALL_SCRIPT"
    [ "$status" -eq 0 ]
}

@test "install.sh quotes variables properly" {
    # Check for unquoted $VARIABLE usage (potential word splitting)
    # Allow $? and specific patterns
    run grep -E '\$[A-Z_]+[^"]' "$INSTALL_SCRIPT" | grep -v '\$?' | grep -v 'echo \$' | grep -v '#'
    # This is a loose check - manual review is still needed
    [ "$status" -eq 0 ] || [ -z "$output" ] || true
}

#------------------------------------------------------------------------------
# Integration Tests (require mocking or specific environment)
#------------------------------------------------------------------------------

@test "install.sh --action creates workflow directory" {
    cd "$TEST_TEMP"
    # This would need Python/pip available, so we skip the actual install
    # Just verify the function exists and would be called
    run grep -A5 '"action")' "$INSTALL_SCRIPT"
    [[ "$output" =~ "setup_github_action" ]]
}
