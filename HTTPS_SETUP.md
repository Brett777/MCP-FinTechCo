# HTTPS Setup with Caddy Reverse Proxy

This guide explains how to set up HTTPS for the MCP-FinTechCo server using Caddy as a reverse proxy.

## Overview

Instead of modifying the MCP server itself, we use Caddy as a reverse proxy that:
- Listens on HTTPS (port 443) with automatic self-signed certificates
- Proxies requests to the MCP server running on HTTP (port 8000)
- Automatically redirects HTTP (port 80) to HTTPS

## Architecture

```
Internet (HTTPS) → Caddy (443) → MCP Server (8000) → Alpha Vantage API
```

## Prerequisites

- Access to the GCP instance via SSH
- The MCP server running on port 8000
- Firewall rules allowing ports 80 and 443

## Installation Steps

### Option 1: Automated Script (Recommended)

1. **Copy the setup script to your GCP instance:**
   ```bash
   gcloud compute scp setup-caddy.sh mcp-server-vm:~ \
     --zone=us-central1-a --project=spherical-wave-170119
   ```

2. **SSH into the instance:**
   ```bash
   gcloud compute ssh mcp-server-vm \
     --zone=us-central1-a --project=spherical-wave-170119
   ```

3. **Run the setup script:**
   ```bash
   chmod +x setup-caddy.sh
   ./setup-caddy.sh
   ```

### Option 2: Manual Installation

1. **SSH into the instance:**
   ```bash
   gcloud compute ssh mcp-server-vm \
     --zone=us-central1-a --project=spherical-wave-170119
   ```

2. **Update system packages:**
   ```bash
   sudo apt-get update -y
   ```

3. **Install Caddy:**
   ```bash
   sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.caddy.community/Caddyfile/caddy.gpg.key' | \
     sudo gpg --dearmor -o /usr/share/keyrings/caddy-archive-keyring.gpg
   curl -1sLf 'https://dl.caddy.community/Caddyfile/debian/caddy.deb.txt' | \
     sudo tee /etc/apt/sources.list.d/caddy-debian.sources
   sudo apt-get update -y
   sudo apt-get install -y caddy
   ```

4. **Create Caddyfile:**
   ```bash
   sudo nano /etc/caddy/Caddyfile
   ```

   Paste the following configuration:
   ```
   # Caddy configuration for MCP-FinTechCo Server
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
   ```

5. **Verify and reload Caddy:**
   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   sudo systemctl status caddy
   ```

## Firewall Configuration

Ensure your GCP firewall allows traffic on ports 80 and 443:

```bash
# Allow HTTP (port 80)
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --project=spherical-wave-170119

# Allow HTTPS (port 443)
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --project=spherical-wave-170119
```

Or update existing rules if they already exist:
```bash
gcloud compute firewall-rules update default-allow-http \
  --allow=tcp:80,tcp:443 \
  --project=spherical-wave-170119
```

## Usage

### Accessing the Server

**Before HTTPS Setup:**
```
http://136.111.134.253:8000/sse
```

**After HTTPS Setup:**
```
https://136.111.134.253/sse
```

### Connecting MCP Client

Update your MCP client configuration to use the new HTTPS endpoint:
```json
{
  "mcpServers": {
    "mcp-fintechco": {
      "command": "sse",
      "url": "https://136.111.134.253"
    }
  }
}
```

### Certificate Warnings

Since we're using self-signed certificates, you may see browser warnings:
- **In browser**: Click "Advanced" → "Proceed to 136.111.134.253"
- **In curl**: Use `curl -k https://136.111.134.253/...` (insecure flag)
- **In Python**: Disable SSL verification for testing
  ```python
  import requests
  response = requests.get(
      'https://136.111.134.253/sse',
      verify=False  # Ignore SSL certificate warnings
  )
  ```

## Troubleshooting

### Check Caddy Status
```bash
sudo systemctl status caddy
```

### View Caddy Logs
```bash
sudo journalctl -u caddy -f
```

### Verify Caddyfile Syntax
```bash
sudo caddy validate --config /etc/caddy/Caddyfile
```

### Reload Configuration
```bash
sudo systemctl reload caddy
```

### Test HTTPS Connection
```bash
# Using curl (ignore SSL warnings)
curl -k https://136.111.134.253/

# Using openssl to check certificate
openssl s_client -connect 136.111.134.253:443
```

## Future: Obtain Real Certificate

To use a real SSL certificate instead of self-signed:

1. **Point a domain to the IP** (e.g., `api.fintechco.com` → `136.111.134.253`)
2. **Update Caddyfile:**
   ```
   api.fintechco.com {
       reverse_proxy localhost:8000 {
           flush_interval -1
       }
   }
   ```
3. **Caddy will automatically obtain a Let's Encrypt certificate**

This eliminates the need for manual certificate management.

## Performance Considerations

- Caddy acts as a lightweight reverse proxy
- SSE (Server-Sent Events) connections are properly forwarded
- Minimal overhead - typically <1ms latency added
- Certificate validation happens in-memory

## Security Notes

⚠️ **Self-Signed Certificate Warning:**
- Suitable for internal testing and development
- Not recommended for production with external users
- Consider obtaining a real certificate for production use
- Self-signed certificates cannot be revoked

## Support

For Caddy documentation: https://caddyserver.com/docs/
For MCP documentation: https://gofastmcp.com/
