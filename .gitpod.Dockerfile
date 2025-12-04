# Gitpod Dockerfile for AutoPR Engine
FROM gitpod/workspace-python-3.12

# Install additional tools
RUN pip install --upgrade pip poetry

# Install bats for testing
RUN sudo apt-get update && \
    sudo apt-get install -y bats shellcheck && \
    sudo rm -rf /var/lib/apt/lists/*

# Set up Poetry to use in-project virtualenv
RUN poetry config virtualenvs.in-project true
