#!/bin/bash
#
# MCP-FinTechCo VM Startup Script
#
# This script runs when a new GCP VM instance is created.
# It installs dependencies and sets up the MCP server.
#
# Usage: This is automatically executed by GCP when creating a VM with:
#   --metadata-from-file=startup-script=startup-script.sh

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
REPO_URL="https://github.com/Brett777/MCP-FinTechCo.git"
INSTALL_DIR="/opt/MCP-FinTechCo"
PYTHON_VERSION="3.11"
LOG_FILE="/var/log/mcp-startup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Starting MCP-FinTechCo server setup..."

# Update system
log "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install essential packages
log "Installing essential packages..."
apt-get install -y \
    software-properties-common \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools

# Install Python 3.11
log "Installing Python $PYTHON_VERSION..."
apt-get install -y \
    python$PYTHON_VERSION \
    python$PYTHON_VERSION-venv \
    python3-pip

# Verify Python installation
python$PYTHON_VERSION --version | tee -a "$LOG_FILE"

# Clone repository
log "Cloning MCP-FinTechCo repository..."
if [ -d "$INSTALL_DIR" ]; then
    log "Directory already exists, pulling latest changes..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Set proper ownership
chown -R $(whoami):$(whoami) "$INSTALL_DIR"

# Create and activate virtual environment
log "Setting up Python virtual environment..."
python$PYTHON_VERSION -m venv venv

# Activate virtual environment and install dependencies
log "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    log "Creating .env file from template..."
    cp .env.sample .env

    # Update production settings
    sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env
    sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=INFO/' .env

    log ".env file created. Please update with production values if needed."
else
    log ".env file already exists, skipping creation."
fi

# Install systemd service
log "Installing systemd service..."
cp mcp-server.service /etc/systemd/system/

# Update service file paths if necessary
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|" /etc/systemd/system/mcp-server.service
sed -i "s|ExecStart=.*|ExecStart=$INSTALL_DIR/venv/bin/python server.py|" /etc/systemd/system/mcp-server.service

# Reload systemd and enable service
log "Enabling MCP server service..."
systemctl daemon-reload
systemctl enable mcp-server.service

# Start the service
log "Starting MCP server..."
systemctl start mcp-server.service

# Wait a moment for service to start
sleep 3

# Check service status
log "Checking service status..."
if systemctl is-active --quiet mcp-server.service; then
    log "MCP server is running successfully!"
    systemctl status mcp-server.service | tee -a "$LOG_FILE"
else
    log "ERROR: MCP server failed to start!"
    journalctl -u mcp-server.service -n 50 | tee -a "$LOG_FILE"
    exit 1
fi

# Display server info
log "Setup complete!"
log "Server installation directory: $INSTALL_DIR"
log "Python version: $(python$PYTHON_VERSION --version)"
log "Service status: $(systemctl is-active mcp-server.service)"
log ""
log "Useful commands:"
log "  - View logs: sudo journalctl -u mcp-server -f"
log "  - Restart server: sudo systemctl restart mcp-server"
log "  - Stop server: sudo systemctl stop mcp-server"
log "  - Check status: sudo systemctl status mcp-server"
log ""
log "Startup script completed successfully!"
