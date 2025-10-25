import asyncio
import subprocess
import time
from loguru import logger
import sys

class SuraAIOrchestrator:
    """Orchestrates all SuraAI agents"""
    
    def __init__(self):
        self.agents = {
            "canary": "agents/canary/canary_agent.py",
            "monitoring": "agents/monitoring/monitoring_agent.py",
            "response": "agents/response/intelligent_response_agent.py",
            "communication": "agents/communication/communication_agent.py"
        }
        self.processes = {}
    
    def start_all_agents(self):
        """Start all agents in separate processes"""
        logger.info("🚀 Starting SuraAI - Autonomous Disaster Recovery Network")
        logger.info("=" * 60)
        
        for name, script in self.agents.items():
            logger.info(f"Starting {name} agent...")
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes[name] = process
            time.sleep(2)  # Give each agent time to start
        
        logger.info("=" * 60)
        logger.info("✅ All agents started successfully!")
        logger.info(f"🐦 Canary Agent: Testing updates before deployment")
        logger.info(f"👁️  Monitoring Agent: Watching all systems 24/7")
        logger.info(f"🚑 Response Agent: Ready for autonomous recovery")
        logger.info(f"📢 Communication Agent: Status updates active")
        logger.info("=" * 60)
    
    def monitor_agents(self):
        """Monitor agent health"""
        try:
            while True:
                time.sleep(5)
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"❌ {name} agent crashed! Restarting...")
                        self.restart_agent(name)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down SuraAI...")
            self.stop_all_agents()
    
    def restart_agent(self, name: str):
        """Restart a crashed agent"""
        script = self.agents[name]
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes[name] = process
        logger.info(f"✅ {name} agent restarted")
    
    def stop_all_agents(self):
        """Stop all agents"""
        for name, process in self.processes.items():
            logger.info(f"Stopping {name} agent...")
            process.terminate()
            process.wait()
        logger.info("👋 All agents stopped")

def main():
    orchestrator = SuraAIOrchestrator()
    orchestrator.start_all_agents()
    orchestrator.monitor_agents()

if __name__ == "__main__":
    main()
