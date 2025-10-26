"""
SuraAI Dashboard API - Minimal version
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
state = {
    "running": False,
    "current_scenario": None,
    "phase": None,
    "active_agents": [],
    "message_flows": [],
    "metrics": {
        "testsRun": 0,
        "badUpdatesCaught": 0,
        "anomaliesDetected": 0,
        "autonomousRecoveries": 0,
        "incidentsPrevented": 0
    },
    "completed_scenarios": []
}

@app.get("/api/status")
async def get_status():
    return state

@app.post("/api/run-tests")
async def run_tests():
    if state["running"]:
        return {"error": "Already running"}
    
    state["running"] = True
    asyncio.create_task(simulate_tests())
    return {"status": "started"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SuraAI Dashboard API"}

async def simulate_tests():
    scenarios = [
        {"id": 1, "name": "Bad Software Update", "icon": "🐦", "problem": "Faulty kernel update", "action": "ROLLBACK"},
        {"id": 2, "name": "CPU Spike", "icon": "📊", "problem": "CPU at 95%", "action": "SCALE_UP"},
        {"id": 3, "name": "Memory Leak", "icon": "🐛", "problem": "Memory leak detected", "action": "RESTART"},
        {"id": 4, "name": "Cascading Failure", "icon": "⚡", "problem": "10 systems failing", "action": "FAILOVER"}
    ]
    
    for scenario in scenarios:
        state["current_scenario"] = scenario
        
        # Detecting
        state["phase"] = "detecting"
        state["active_agents"] = ["monitoring"]
        state["metrics"]["anomaliesDetected"] += 1
        await asyncio.sleep(3)
        
        # Assessing
        state["phase"] = "assessing"
        state["active_agents"] = ["monitoring", "response"]
        state["message_flows"] = [{"from": "monitoring", "to": "response"}]
        await asyncio.sleep(4)
        
        # Executing
        state["phase"] = "executing"
        state["active_agents"] = ["response"]
        state["metrics"]["autonomousRecoveries"] += 1
        if scenario["id"] == 1:
            state["metrics"]["badUpdatesCaught"] += 1
            state["metrics"]["incidentsPrevented"] += 1
        await asyncio.sleep(3)
        
        # Notifying
        state["phase"] = "notifying"
        state["active_agents"] = ["communication"]
        state["message_flows"] = [{"from": "response", "to": "communication"}]
        await asyncio.sleep(2)
        
        # Resolved
        state["phase"] = "resolved"
        state["active_agents"] = []
        state["message_flows"] = []
        state["completed_scenarios"].append(scenario["id"])
        state["metrics"]["testsRun"] += 1
        await asyncio.sleep(2)
    
    state["running"] = False
    state["current_scenario"] = None

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SuraAI Dashboard API")
    print("📊 API: http://localhost:3001")
    print("🔌 Health: http://localhost:3001/health")
    uvicorn.run(app, host="0.0.0.0", port=3001)