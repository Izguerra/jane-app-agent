#!/bin/bash
set -e

# ==========================================
# JaneApp Agent - Telephony Deployment Script
# ==========================================

# 0. Fix Broken Mirrors (EOL Release -> Old Releases)
echo "Fixing APT Mirrors (EOL Release)..."
# Remove the legacy file we created to stop duplicates
sudo rm -f /etc/apt/sources.list

# Backup existing modern sources file
sudo cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.bak || true

# Overwrite ubuntu.sources with old-releases mirrors (Deb822 format)
cat <<EOF | sudo tee /etc/apt/sources.list.d/ubuntu.sources
Types: deb
URIs: http://old-releases.ubuntu.com/ubuntu/
Suites: oracular oracular-updates oracular-backports oracular-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

# Nuke old lists to prevent 404s
sudo rm -rf /var/lib/apt/lists/*
sudo apt-get clean

# 1. Update System & Install Dependencies
echo "Update System..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release ufw

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "Docker already installed."
fi

# 2.5 Install Python Dependencies (For ARI Controller)
echo "Installing Python Dependencies..."
sudo apt-get install -y python3-pip python3-venv
# Create venv for isolation
python3 -m venv ~/supaagent_telephony/venv
~/supaagent_telephony/venv/bin/pip install asyncari httpx anyio

# 3. Configure Firewall (UFW) - DISABLED FOR SHARED SERVER SAFETY
# echo "Configuring Firewall..."
# sudo ufw allow 22/tcp       # SSH
# sudo ufw allow 5060/tcp     # SIP Signaling (TCP)
# sudo ufw allow 5060/udp     # SIP Signaling (UDP)
# sudo ufw allow 10000:10020/udp # RTP Audio Range
# sudo ufw --force enable

# 4. Setup Directory Structure
echo "Setting up Directories..."
mkdir -p ~/supaagent_telephony/backend/asterisk_config
mkdir -p ~/supaagent_telephony/backend/services

# 5. Instructions only (Files need to be copied via SCP)
echo "=========================================="
echo "Server Configured!"
echo "Now copy your local files to this server:"
echo "scp -r backend/asterisk_config root@<ServerIP>:~/supaagent_telephony/backend/"
echo "scp backend/services/ari_controller.py root@<ServerIP>:~/supaagent_telephony/backend/services/"
echo "scp docker-compose.yml root@<ServerIP>:~/supaagent_telephony/"
echo "=========================================="
