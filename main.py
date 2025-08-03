import threading
from gui import App
import server

if __name__ == "__main__":
    print("[*] Starting C2 server in the background...")
    server_thread = threading.Thread(target=server.run_server, daemon=True)
    server_thread.start()
    
    print("[*] Launching Live Actions C2 Panel...")
    app = App()
    app.mainloop()