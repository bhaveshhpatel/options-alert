#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker
sudo mkdir -p /opt/options-alert/data/runtime
sudo chown -R "$USER":"$USER" /opt/options-alert
if [ ! -d /opt/options-alert/repo ]; then
  git clone https://github.com/bhaveshhpatel/options-alert.git /opt/options-alert/repo
else
  git -C /opt/options-alert/repo pull --ff-only
fi
ln -sfn /opt/options-alert/data/runtime /opt/options-alert/repo/data/runtime
echo 'Bootstrap complete. Log out/in once so the docker group membership takes effect.'
