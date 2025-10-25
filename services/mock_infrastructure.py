from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import random
import time
from loguru import logger

app = FastAPI(title="SuraAI Mock Infrastructure")

# Simulated systems
systems = {f"server-{i}": {
    "status": "healthy",
    "cpu": random.uniform(20, 40),
    "memory": random.uniform(30, 50),
    "version": "1.0.0",
    "last_update": None
} for i in range(100)}

class UpdateRequest(BaseModel):
    update_id: str
    version: str
    target_systems: List[str]

class SystemStatus(BaseModel):
    system_id: str
    status: str
    metrics: Dict[str, float]

@app.get("/")
def root():
    return {"service": "SuraAI Mock Infrastructure", "systems": len(systems)}

@app.get("/systems")
def get_systems():
    """Get all systems"""
    return {"systems": list(systems.keys()), "total": len(systems)}

@app.get("/system/{system_id}")
def get_system(system_id: str):
    """Get specific system status"""
    if system_id not in systems:
        raise HTTPException(status_code=404, detail="System not found")
    return systems[system_id]

@app.post("/deploy")
def deploy_update(update: UpdateRequest):
    """Deploy update to systems"""
    logger.info(f"Deploying {update.update_id} to {len(update.target_systems)} systems")
    
    # Simulate deployment
    deployed = []
    failed = []
    
    for sys_id in update.target_systems:
        if sys_id in systems:
            # 5% chance of failure for demo
            if random.random() < 0.05:
                systems[sys_id]["status"] = "failed"
                failed.append(sys_id)
            else:
                systems[sys_id]["version"] = update.version
                systems[sys_id]["last_update"] = time.time()
                deployed.append(sys_id)
    
    return {
        "update_id": update.update_id,
        "deployed": len(deployed),
        "failed": len(failed),
        "failed_systems": failed
    }

@app.post("/rollback/{system_id}")
def rollback_system(system_id: str):
    """Rollback a system"""
    if system_id not in systems:
        raise HTTPException(status_code=404, detail="System not found")
    
    systems[system_id]["version"] = "1.0.0"
    systems[system_id]["status"] = "healthy"
    logger.info(f"Rolled back {system_id}")
    
    return {"system_id": system_id, "status": "rolled_back"}

@app.post("/simulate-failure/{system_id}")
def simulate_failure(system_id: str):
    """Simulate a failure for testing"""
    if system_id not in systems:
        raise HTTPException(status_code=404, detail="System not found")
    
    systems[system_id]["status"] = "failed"
    systems[system_id]["cpu"] = 95.0
    systems[system_id]["memory"] = 98.0
    
    logger.warning(f"Simulated failure on {system_id}")
    return {"system_id": system_id, "status": "failure_simulated"}

@app.get("/health")
def health():
    """Health check"""
    healthy = sum(1 for s in systems.values() if s["status"] == "healthy")
    return {
        "total_systems": len(systems),
        "healthy": healthy,
        "unhealthy": len(systems) - healthy
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
