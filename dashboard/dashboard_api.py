"""
Dashboard API - Serves the web dashboard and triggers test pipeline
Run: python dashboard_api.py
Then open: http://localhost:3000
"""

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import subprocess
import json
from pathlib import Path
from loguru import logger
import os

app = FastAPI(title="SuraAI Dashboard API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store test state
test_state = {
    "running": False,
    "current_scenario": None,
    "metrics": {
        "testsRun": 0,
        "badUpdatesCaught": 0,
        "anomaliesDetected": 0,
        "autonomousRecoveries": 0,
        "incidentsPrevented": 0
    }
}

@app.get("/")
async def root():
    """Serve the dashboard HTML"""
    dashboard_path = Path("dashboard/index.html")
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"error": "Dashboard not found. Create dashboard/index.html"}

@app.get("/api/status")
async def get_status():
    """Get current test status"""
    return test_state

@app.post("/api/run-tests")
async def run_tests():
    """Trigger the actual test pipeline"""
    if test_state["running"]:
        return {"error": "Tests already running"}
    
    test_state["running"] = True
    test_state["metrics"] = {
        "testsRun": 0,
        "badUpdatesCaught": 0,
        "anomaliesDetected": 0,
        "autonomousRecoveries": 0,
        "incidentsPrevented": 0
    }
    
    # Start test pipeline in background
    asyncio.create_task(run_test_pipeline())
    
    return {"status": "started"}

async def run_test_pipeline():
    """Actually run the e2e_test_pipeline.py"""
    try:
        logger.info("🚀 Starting real test pipeline...")
        
        # Check if mock infrastructure is running
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    if resp.status != 200:
                        logger.error("Mock infrastructure not running!")
                        test_state["running"] = False
                        return
        except:
            logger.error("Mock infrastructure not running!")
            test_state["running"] = False
            return
        
        # Run the actual test pipeline
        process = await asyncio.create_subprocess_exec(
            "python", "e2e_test_pipeline.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Monitor output and update metrics
        async for line in process.stdout:
            line = line.decode().strip()
            logger.info(line)
            
            # Parse metrics from output
            if "SCENARIO" in line:
                test_state["current_scenario"] = line
                test_state["metrics"]["testsRun"] += 1
            elif "Bad Updates Caught" in line:
                test_state["metrics"]["badUpdatesCaught"] += 1
            elif "Anomalies Detected" in line:
                test_state["metrics"]["anomaliesDetected"] += 1
            elif "Autonomous Recoveries" in line:
                test_state["metrics"]["autonomousRecoveries"] += 1
            elif "Incidents Prevented" in line:
                test_state["metrics"]["incidentsPrevented"] += 1
        
        await process.wait()
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
    finally:
        test_state["running"] = False
        test_state["current_scenario"] = None
        logger.info("✅ Test pipeline completed")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send current state every second
            await websocket.send_json(test_state)
            await asyncio.sleep(1)
    except:
        pass

@app.get("/api/logs")
async def get_logs():
    """Get recent logs from log files"""
    logs = []
    log_dir = Path("logs")
    
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                    logs.extend([{
                        "file": log_file.name,
                        "line": line.strip()
                    } for line in lines])
            except:
                pass
    
    return {"logs": logs[-100:]}  # Return last 100 total

@app.get("/api/agent-registry")
async def get_agent_registry():
    """Get registered agents"""
    registry_file = Path("agent_registry.json")
    if registry_file.exists():
        with open(registry_file, 'r') as f:
            return json.load(f)
    return {}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "SuraAI Dashboard API"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting SuraAI Dashboard API")
    logger.info("📊 Dashboard: http://localhost:3000")
    logger.info("🔌 API Docs: http://localhost:3000/docs")
    uvicorn.run(app, host="0.0.0.0", port=3000)