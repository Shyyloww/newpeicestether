import threading
from gui import App
import server  # <-- 1. Imports the server code

if __name__ == "__main__":
    # --- This block starts the server ---
    print("[*] Starting C2 server in the background...")
    # 2. Creates a separate thread to run the server's main function
    server_thread = threading.Thread(target=server.run_server, daemon=True)
    # 3. Starts the server thread. It now runs in the background.
    server_thread.start()
    
    # --- This block starts the GUI ---
    print("[*] Launching Live Actions C2 Panel...")
    # 4. Creates and runs the GUI application in the main thread.
    app = App()
    app.mainloop()