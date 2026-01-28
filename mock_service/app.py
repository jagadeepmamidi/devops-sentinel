from flask import Flask, jsonify
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / 'mock_log.txt'

def log_message(level, message):
    """Appends a message to the log file."""
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.utcnow().isoformat()} - {level} - {message}\n")

@app.route('/')
def health_check():
    """
    Checks the service health.
    - If 'db_down.txt' exists, it simulates a database connection error.
    - If 'break.txt' exists, it simulates a generic application error.
    - Otherwise, it's healthy.
    """
    if (SCRIPT_DIR / 'db_down.txt').exists():
        log_message("ERROR", "Failed to connect to primary database.")
        return jsonify({
            "status": "error",
            "message": "Internal Server Error: Database connection failed"
        }), 500
    
    if (SCRIPT_DIR / 'break.txt').exists():
        log_message("ERROR", "Unhandled exception in payment processing module.")
        return jsonify({
            "status": "error", 
            "message": "Internal Server Error: Application logic failed"
        }), 500
    
    log_message("INFO", "Health check successful.")
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Ensure log file exists
    with open(LOG_FILE, 'w') as f:
        f.write(f"{datetime.utcnow().isoformat()} - INFO - Mock Service starting up.\n")
    app.run(port=8000, debug=True)