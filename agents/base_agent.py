from uagents import Agent, Context, Model
from loguru import logger
import os
from typing import Optional, Dict, Any, List
from agents.registry import register_agent, get_agent_address, registry # Keep registry import

# Note: load_dotenv() should be called at the top of each agent's main file (e.g., canary_agent.py)
# but for simplicity, we'll keep it here for guaranteed access to OS environment variables.
from dotenv import load_dotenv

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
    def __init__(
        self, 
        name: str, 
        seed: str, 
        port: int, 
        capabilities: List[str] = None,
        endpoint: Optional[str] = None
    ):
        load_dotenv()
        
        # 🎯 FIX 1: Initialize for Mailbox mode. 
        # Setting mailbox=True ensures Agentverse can route messages to you.
        # We also keep the local port for local-to-local communication
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            mailbox=True, 
            endpoint=None
        )
        self.name = name
        self.capabilities = capabilities or []
        
        # Setup logging
        logger.add(
            f"logs/{name}.log",
            rotation="100 MB",
            retention="7 days",
            level="INFO"
        )
        
        logger.info(f"✅ {name} initialized (Mailbox mode enabled)")
        logger.info(f"   Address: {self.agent.address}")
        logger.info(f"   Port: {port}")
        
        # Auto-register in registry
        self.register_self()
    
    def register_self(self):
        """Register this agent in the global registry"""
        try:
            register_agent(
                name=self.name,
                address=str(self.agent.address),
                port=self.agent._port,
                capabilities=self.capabilities
            )
            logger.info(f"📝 Registered {self.name} in agent registry")
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
    
    def get_peer_address(self, peer_name: str) -> Optional[str]:
        """Get another agent's address from registry"""
        # This function fetches the local address for local-to-local agent communication
        address = get_agent_address(peer_name) 
        if address:
            logger.debug(f"Found {peer_name} at {address[:20]}...")
        else:
            logger.warning(f"Agent {peer_name} not found in registry")
        return address
    
    async def send_to_peer(self, ctx: Context, peer_name: str, message: Model) -> bool:
        """
        🎯 FIX 2: Revert to standard uAgents routing (ctx.send).
        This method automatically handles all routing: local HTTP, remote Mailbox, or Almanac.
        """
        address = self.get_peer_address(peer_name)
        if not address:
            logger.error(f"❌ Cannot send to {peer_name} - not in registry")
            return False
        
        try:
            # Use the standard uagents send function
            await ctx.send(address, message)
            logger.info(f"✅ Sent {message.__class__.__name__} to {peer_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send to {peer_name}: {e}")
            return False
    
    def get_agent(self):
        return self.agent
    
    def get_address(self):
        return self.agent.address