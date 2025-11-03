# MCP-FinTechCo Deployment Guide

This guide provides detailed instructions for deploying the MCP-FinTechCo server to Google Cloud Platform.

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Account** with billing enabled
2. **Google Cloud CLI** installed and configured
3. **GitHub CLI** (for repository management)
4. **Local Testing** completed successfully

## Quick Deployment

For experienced users:

```bash
./deploy.sh
```

This automated script handles the entire deployment process.

## Manual Deployment Steps

### 1. Google Cloud Setup

#### Install and Initialize gcloud CLI

If not already installed:

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

**Linux/Mac:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Initialize:**
```bash
gcloud init
```

#### Set Up GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable logging.googleapis.com
```

### 2. Create and Configure VM Instance

#### Create e2-small VM in us-central1

```bash
gcloud compute instances create mcp-server-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=e2-small \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=mcp-server,http-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=mcp-server-vm,image=projects/debian-cloud/global/images/debian-12-bookworm-v20250110,mode=rw,size=10,type=pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,application=mcp-server \
    --reservation-affinity=any \
    --metadata-from-file=startup-script=startup-script.sh
```

#### Create Firewall Rule

```bash
gcloud compute firewall-rules create allow-mcp-server \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:8000 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=mcp-server
```

**Note:** For production, restrict `--source-ranges` to specific IP addresses.

### 3. SSH Access

#### Generate SSH Key (if needed)

```bash
ssh-keygen -t rsa -f ~/.ssh/gcp-mcp-server -C "your-email@example.com"
```

#### Add SSH Key to VM

```bash
gcloud compute instances add-metadata mcp-server-vm \
    --zone=us-central1-a \
    --metadata-from-file ssh-keys=~/.ssh/gcp-mcp-server.pub
```

#### Connect to VM

```bash
gcloud compute ssh mcp-server-vm --zone=us-central1-a
```

### 4. Server Installation on VM

Once connected to the VM:

#### Install Python 3.11

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y software-properties-common build-essential

# Add deadsnakes PPA (for Ubuntu) or install from source
# For Debian 12, Python 3.11 should be available:
sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### Clone Repository

```bash
# Install git if needed
sudo apt install -y git

# Clone your repository
cd /opt
sudo git clone https://github.com/YOUR-USERNAME/MCP-FinTechCo.git
sudo chown -R $USER:$USER MCP-FinTechCo
cd MCP-FinTechCo
```

#### Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
# Copy sample env file
cp .env.sample .env

# Edit with your settings
nano .env
```

Update the following in `.env`:
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
MCP_SERVER_PORT=8000
```

#### Test Server Manually

```bash
# Run server to test
python server.py
```

Press `Ctrl+C` to stop after verifying it starts correctly.

### 5. Set Up Systemd Service

#### Install Service File

```bash
# Copy service file to systemd
sudo cp mcp-server.service /etc/systemd/system/

# Update paths in service file if necessary
sudo nano /etc/systemd/system/mcp-server.service
```

Verify paths in the service file match your installation:
- `WorkingDirectory=/opt/MCP-FinTechCo`
- `ExecStart=/opt/MCP-FinTechCo/venv/bin/python server.py`

#### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable mcp-server

# Start the service
sudo systemctl start mcp-server

# Check status
sudo systemctl status mcp-server
```

### 6. Verify Deployment

#### Check Service Status

```bash
# View service status
sudo systemctl status mcp-server

# View logs
sudo journalctl -u mcp-server -f
```

#### Test from Local Machine

Get your VM's external IP:
```bash
gcloud compute instances describe mcp-server-vm \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Test the endpoint (adjust based on your MCP client):
```bash
# Example with curl (adjust for actual MCP protocol)
curl http://EXTERNAL_IP:8000
```

## Monitoring and Maintenance

### View Logs

```bash
# Real-time logs
sudo journalctl -u mcp-server -f

# Last 100 lines
sudo journalctl -u mcp-server -n 100

# Logs from today
sudo journalctl -u mcp-server --since today
```

### Restart Service

```bash
sudo systemctl restart mcp-server
```

### Update Server

```bash
# SSH to VM
gcloud compute ssh mcp-server-vm --zone=us-central1-a

# Navigate to project
cd /opt/MCP-FinTechCo

# Pull latest changes
git pull

# Activate venv
source venv/bin/activate

# Update dependencies if needed
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart mcp-server
```

### Stop Server

```bash
sudo systemctl stop mcp-server
```

## Cost Optimization

### e2-small VM Costs (us-central1)

- **Monthly (730 hours):** ~$12-15 USD
- **Per hour:** ~$0.017 USD

### Cost-Saving Tips

1. **Stop VM when not in use:**
   ```bash
   gcloud compute instances stop mcp-server-vm --zone=us-central1-a
   ```

2. **Start VM when needed:**
   ```bash
   gcloud compute instances start mcp-server-vm --zone=us-central1-a
   ```

3. **Use committed use discounts** for long-term deployments

4. **Monitor usage:**
   ```bash
   gcloud compute instances describe mcp-server-vm --zone=us-central1-a
   ```

## Troubleshooting

### Server Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u mcp-server -n 50
   ```

2. Verify Python version:
   ```bash
   /opt/MCP-FinTechCo/venv/bin/python --version
   ```

3. Check environment file:
   ```bash
   cat /opt/MCP-FinTechCo/.env
   ```

4. Test manually:
   ```bash
   cd /opt/MCP-FinTechCo
   source venv/bin/activate
   python server.py
   ```

### Connection Issues

1. Verify firewall rule:
   ```bash
   gcloud compute firewall-rules describe allow-mcp-server
   ```

2. Check VM external IP:
   ```bash
   gcloud compute instances describe mcp-server-vm \
       --zone=us-central1-a \
       --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
   ```

3. Verify port is listening:
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/MCP-FinTechCo

# Fix service permissions
sudo chmod 644 /etc/systemd/system/mcp-server.service
sudo systemctl daemon-reload
```

## Security Best Practices

1. **Restrict firewall rules** to specific IP ranges
2. **Use HTTPS** with SSL/TLS certificates (consider Cloud Load Balancer)
3. **Regular updates:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
4. **Monitor access logs** regularly
5. **Use service accounts** with minimal permissions
6. **Enable Cloud Logging** for audit trails
7. **Implement rate limiting** in production

## Backup and Recovery

### Backup Configuration

```bash
# SSH to VM
gcloud compute ssh mcp-server-vm --zone=us-central1-a

# Backup .env file (store securely)
cp /opt/MCP-FinTechCo/.env ~/mcp-backup-env-$(date +%Y%m%d).txt
```

### Create VM Snapshot

```bash
gcloud compute disks snapshot mcp-server-vm \
    --snapshot-names=mcp-server-snapshot-$(date +%Y%m%d) \
    --zone=us-central1-a
```

### Restore from Snapshot

```bash
gcloud compute disks create mcp-server-restored \
    --source-snapshot=mcp-server-snapshot-YYYYMMDD \
    --zone=us-central1-a
```

## Additional Resources

- [Google Cloud Compute Documentation](https://cloud.google.com/compute/docs)
- [FastMCP Documentation](https://gofastmcp.com)
- [GCP Free Tier](https://cloud.google.com/free)

## Support

For deployment issues:
1. Check troubleshooting section above
2. Review logs on VM
3. Consult GCP documentation
4. Open issue on GitHub repository
