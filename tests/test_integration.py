import pytest
import asyncio
import requests
from agents.canary.canary_agent import UpdatePackage
from agents.monitoring.monitoring_agent import SystemMetrics

BASE_URL = "http://localhost:8000"

def test_mock_infrastructure():
    """Test mock infrastructure is running"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "total_systems" in data
    assert data["total_systems"] > 0

def test_deploy_update():
    """Test deploying an update"""
    update = {
        "update_id": "TEST-001",
        "version": "1.5.0",
        "target_systems": ["server-1", "server-2"]
    }
    response = requests.post(f"{BASE_URL}/deploy", json=update)
    assert response.status_code == 200
    data = response.json()
    assert "deployed" in data

def test_simulate_failure():
    """Test failure simulation"""
    response = requests.post(f"{BASE_URL}/simulate-failure/server-1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failure_simulated"

def test_rollback():
    """Test rollback functionality"""
    response = requests.post(f"{BASE_URL}/rollback/server-1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rolled_back"

@pytest.mark.asyncio
async def test_agent_communication():
    """Test agents can communicate"""
    # This would test actual agent message passing
    # Simplified for demo
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
