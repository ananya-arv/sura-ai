#!/usr/bin/env python3
"""
SuraAI Live Dashboard API
Serves real-time status and logs for the monitoring dashboard
"""

from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global state lock for thread safety
state_lock = threading.Lock()

# Global state
system_state = {
    "running": False,
    "current_scenario": None,
    "phase": None,  # "detecting", "assessing", "executing"
    "active_agents": [],
    "message_flows": [],
    "metrics": {
        "testsRun": 0,
        "badUpdatesCaught": 0,
        "anomaliesDetected": 0,
        "autonomousRecoveries": 0,
        "incidentsPrevented": 0,
    },
    "completed_scenarios": [],
    "logs": []
}

test_thread = None

def reset_state():
    """Reset system state for new test run"""
    global system_state
    with state_lock:
        system_state.update({
            "running": True,
            "current_scenario": None,
            "phase": None,
            "active_agents": [],
            "message_flows": [],
            "completed_scenarios": [],
            "logs": [],
            "metrics": {
                "testsRun": 0,
                "badUpdatesCaught": 0,
                "anomaliesDetected": 0,
                "autonomousRecoveries": 0,
                "incidentsPrevented": 0,
            }
        })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system state"""
    with state_lock:
        return jsonify(system_state)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent logs (newest first)"""
    with state_lock:
        logs = system_state.get("logs", [])[-50:]  # Last 50 logs
    return jsonify(logs)

@app.route('/api/run-tests', methods=['POST'])
def run_tests():
    """Start the test pipeline"""
    global test_thread

    with state_lock:
        if system_state["running"]:
            return jsonify({"error": "Tests already running"}), 400

    reset_state()

    # Run test pipeline in background thread
    test_thread = threading.Thread(target=run_test_pipeline, daemon=True)
    test_thread.start()

    return jsonify({"message": "Test pipeline started"})

def update_state(updates):
    """Thread-safe state update"""
    with state_lock:
        system_state.update(updates)

def add_log(log_type, message, agent=None):
    """Add a log entry (thread-safe)"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": log_type,
        "message": message,
    }
    if agent:
        log_entry["agent"] = agent

    with state_lock:
        system_state["logs"].insert(0, log_entry)  # Add to beginning
        # Keep only last 100 logs
        if len(system_state["logs"]) > 100:
            system_state["logs"] = system_state["logs"][:100]

def run_test_pipeline():
    """Run the E2E test pipeline with realistic timing - inline implementation"""
    try:
        from e2e_test_pipeline import run_pipeline_with_api
        run_pipeline_with_api(update_state, add_log)
    except Exception as e:
        print(f"Error running test pipeline: {e}")
        add_log("error", f"Pipeline error: {str(e)}")
    finally:
        update_state({"running": False})
        add_log("success", "Test pipeline completed")

if __name__ == '__main__':
    print("🚀 SuraAI Dashboard API starting on http://localhost:3001")
    print("Frontend should connect to this server")
    print("\nEndpoints:")
    print("  GET  /api/status - Get system state")
    print("  GET  /api/logs   - Get recent logs")
    print("  POST /api/run-tests - Start test pipeline")
    app.run(host='0.0.0.0', port=3001, debug=False, threaded=True)
