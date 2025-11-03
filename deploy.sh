#!/bin/bash
#
# MCP-FinTechCo Automated Deployment Script
#
# This script automates the deployment of MCP-FinTechCo server to Google Cloud Platform.
# It creates a VM instance, configures firewall rules, and sets up the server.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - GitHub repository created and pushed
#   - startup-script.sh properly configured with your repository URL
#
# Usage: ./deploy.sh

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Update these values
PROJECT_ID="${GCP_PROJECT_ID:-}"
ZONE="us-central1-a"
REGION="us-central1"
INSTANCE_NAME="mcp-server-vm"
MACHINE_TYPE="e2-small"
DISK_SIZE="10GB"

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

print_header() {
    echo ""
    print_msg "$BLUE" "=============================================="
    print_msg "$BLUE" "$*"
    print_msg "$BLUE" "=============================================="
    echo ""
}

print_success() {
    print_msg "$GREEN" "✓ $*"
}

print_error() {
    print_msg "$RED" "✗ $*"
}

print_warning() {
    print_msg "$YELLOW" "⚠ $*"
}

print_info() {
    print_msg "$BLUE" "ℹ $*"
}

# Check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed!"
        print_info "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    print_success "gcloud CLI found"
}

# Check if user is authenticated
check_auth() {
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        print_error "Not authenticated with gcloud!"
        print_info "Run: gcloud auth login"
        exit 1
    fi
    print_success "gcloud authentication verified"
}

# Get or set project ID
setup_project() {
    if [ -z "$PROJECT_ID" ]; then
        # Try to get current project
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")

        if [ -z "$PROJECT_ID" ]; then
            print_warning "No GCP project configured"
            read -p "Enter your GCP Project ID: " PROJECT_ID

            if [ -z "$PROJECT_ID" ]; then
                print_error "Project ID is required!"
                exit 1
            fi
        fi
    fi

    gcloud config set project "$PROJECT_ID"
    print_success "Using project: $PROJECT_ID"
}

# Enable required APIs
enable_apis() {
    print_info "Enabling required GCP APIs..."

    gcloud services enable compute.googleapis.com --project="$PROJECT_ID"
    gcloud services enable logging.googleapis.com --project="$PROJECT_ID"

    print_success "APIs enabled"
}

# Check if instance already exists
check_instance_exists() {
    if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" &> /dev/null; then
        print_warning "Instance '$INSTANCE_NAME' already exists!"
        read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deleting existing instance..."
            gcloud compute instances delete "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --quiet
            print_success "Instance deleted"
        else
            print_info "Skipping instance creation. Updating existing instance..."
            return 1
        fi
    fi
    return 0
}

# Create VM instance
create_instance() {
    print_info "Creating VM instance: $INSTANCE_NAME"
    print_info "Machine type: $MACHINE_TYPE in $ZONE"

    gcloud compute instances create "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
        --tags=mcp-server,http-server \
        --create-disk=auto-delete=yes,boot=yes,device-name="$INSTANCE_NAME",image=projects/debian-cloud/global/images/debian-12-bookworm-v20251014,mode=rw,size=10,type=pd-balanced \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=environment=production,application=mcp-server \
        --reservation-affinity=any \
        --metadata-from-file=startup-script=startup-script.sh

    print_success "VM instance created successfully"
}

# Create firewall rule
create_firewall() {
    print_info "Creating firewall rule..."

    # Check if firewall rule exists
    if gcloud compute firewall-rules describe allow-mcp-server --project="$PROJECT_ID" &> /dev/null; then
        print_warning "Firewall rule already exists, skipping..."
        return 0
    fi

    gcloud compute firewall-rules create allow-mcp-server \
        --project="$PROJECT_ID" \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:8000 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=mcp-server

    print_warning "Firewall allows access from anywhere (0.0.0.0/0)"
    print_warning "For production, restrict to specific IPs!"
    print_success "Firewall rule created"
}

# Get instance IP
get_instance_ip() {
    print_info "Retrieving instance external IP..."

    EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

    print_success "External IP: $EXTERNAL_IP"
}

# Wait for startup script to complete
wait_for_startup() {
    print_info "Waiting for startup script to complete (this may take 2-3 minutes)..."

    sleep 60  # Give it a minute to start

    for i in {1..12}; do
        print_info "Checking server status (attempt $i/12)..."

        # Check if service is active via SSH
        if gcloud compute ssh "$INSTANCE_NAME" \
            --zone="$ZONE" \
            --project="$PROJECT_ID" \
            --command="sudo systemctl is-active mcp-server" &> /dev/null; then
            print_success "Server is up and running!"
            return 0
        fi

        sleep 10
    done

    print_warning "Could not verify server status automatically"
    print_info "Check manually with: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
}

# Display final information
show_summary() {
    print_header "Deployment Complete!"

    echo "Instance Details:"
    echo "  Name: $INSTANCE_NAME"
    echo "  Zone: $ZONE"
    echo "  External IP: $EXTERNAL_IP"
    echo "  Machine Type: $MACHINE_TYPE"
    echo ""
    echo "Server URL: http://$EXTERNAL_IP:8000"
    echo ""
    echo "Useful Commands:"
    echo "  SSH to server:"
    echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
    echo ""
    echo "  View logs:"
    echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u mcp-server -f'"
    echo ""
    echo "  Restart server:"
    echo "    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo systemctl restart mcp-server'"
    echo ""
    echo "  Stop VM (to save costs):"
    echo "    gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
    echo ""
    echo "  Start VM:"
    echo "    gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
    echo ""
    echo "  Delete VM:"
    echo "    gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE"
    echo ""
}

# Main deployment flow
main() {
    print_header "MCP-FinTechCo Deployment Script"

    print_info "Starting deployment process..."

    # Pre-flight checks
    check_gcloud
    check_auth
    setup_project
    enable_apis

    # Deployment
    if check_instance_exists; then
        create_instance
    fi

    create_firewall
    get_instance_ip
    wait_for_startup
    show_summary

    print_success "Deployment completed successfully!"
}

# Run main function
main
