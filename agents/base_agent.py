from uagents import Agent, Context, Model
from loguru import logger
import asyncio
from typing import Optional, Dict, Any

class BaseAgentConfig(Model):
    """Base configuration for all agents"""
    agent_name: str
    agent_description: str
    seed_phrase: Optional[str] = None

class AgentMessage(Model):
    """Standard message format between agents"""
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float

class BaseSuraAgent:
    def __init__(self, name: str, seed: str, port: int, endpoint: Optional[str] = None):
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            endpoint=endpoint or f"http://localhost:{port}/submit"
        )
        self.name = name
        
        # Setup logging
        logger.add(
            f"logs/{name}.log",
            rotation="100 MB",
            retention="7 days",
            level="INFO"
        )
        
        logger.info(f"{name} initialized with address: {self.agent.address}")
    
    def get_agent(self):
        return self.agent
    
    def get_address(self):
        return self.agent.address
