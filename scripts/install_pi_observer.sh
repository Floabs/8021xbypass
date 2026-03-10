#!/bin/bash
set -euo pipefail

APP_DIR="/opt/new8021x"
SERVICE_NAME="new8021x-observe.service"
ENV_FILE="/etc/default/new8021x-observe"

echo "[*] Installing Raspberry Pi observer prerequisites"
apt-get update
apt-get install -y python3-venv python3-full iproute2 ethtool tcpdump

echo "[*] Creating application directory"
mkdir -p "${APP_DIR}"

echo "[*] Copying project files"
cp -R . "${APP_DIR}"

echo "[*] Creating virtual environment"
python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install -e "${APP_DIR}"

echo "[*] Installing default environment file if missing"
if [ ! -f "${ENV_FILE}" ]; then
  install -m 0644 "${APP_DIR}/deploy/systemd/new8021x-observe.env.example" "${ENV_FILE}"
fi

echo "[*] Installing systemd service"
install -m 0644 "${APP_DIR}/deploy/systemd/${SERVICE_NAME}" "/etc/systemd/system/${SERVICE_NAME}"
systemctl daemon-reload

echo "[*] Install complete"
echo "[*] Review ${ENV_FILE}, then enable the service with:"
echo "    sudo systemctl enable --now ${SERVICE_NAME}"

