#!/bin/bash
# Caddy Reverse Proxy Setup for MCP-FinTechCo Server
# This script installs Caddy and configures it as an HTTPS reverse proxy

set -e

echo "=========================================="
echo "Installing Caddy Reverse Proxy"
echo "=========================================="

# Update system packages
echo "Updating system packages..."
sudo apt-get update -y

# Install Caddy (official Debian repository)
echo "Installing Caddy..."
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.caddy.community/Caddyfile/caddy.gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-archive-keyring.gpg
curl -1sLf 'https://dl.caddy.community/Caddyfile/debian/caddy.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-debian.sources
sudo apt-get update -y
sudo apt-get install -y caddy

echo "Caddy installed successfully!"

# Check Caddy version
caddy version

# Create Caddyfile for reverse proxy
echo "Creating Caddyfile..."
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
# Caddy configuration for MCP-FinTechCo Server
# Reverse proxy to http://localhost:8000 with automatic HTTPS

:443 {
    # Enable automatic HTTPS with self-signed certificates
    tls internal

    # Reverse proxy to the MCP server running on port 8000
    reverse_proxy localhost:8000 {
        # Keep SSE connections alive
        flush_interval -1

        # Headers for streaming
        header_up Connection "upgrade"
        header_up Upgrade "websocket"
    }
}

# Redirect HTTP to HTTPS
:80 {
    redir https://{host}{uri} permanent
}
EOF

echo "Caddyfile created at /etc/caddy/Caddyfile"

# Verify Caddyfile syntax
echo "Verifying Caddyfile syntax..."
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy to apply new configuration
echo "Reloading Caddy service..."
sudo systemctl reload caddy

# Check Caddy service status
echo "Checking Caddy service status..."
sudo systemctl status caddy --no-pager

echo ""
echo "=========================================="
echo "Caddy Reverse Proxy Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration Details:"
echo "  - HTTPS Port: 443 (automatic self-signed certificate)"
echo "  - HTTP Port: 80 (redirects to HTTPS)"
echo "  - Backend Server: http://localhost:8000"
echo "  - Certificate Type: Internal (self-signed)"
echo ""
echo "Accessing the server:"
echo "  - HTTPS: https://136.111.134.253/"
echo "  - HTTP: http://136.111.134.253/ (redirects to HTTPS)"
echo ""
echo "Note: Browser will warn about self-signed certificate - this is expected"
echo "Click 'Advanced' and proceed to use the server."
echo ""
echo "To view logs: sudo journalctl -u caddy -f"
echo "To edit config: sudo nano /etc/caddy/Caddyfile"
echo "To reload: sudo systemctl reload caddy"
