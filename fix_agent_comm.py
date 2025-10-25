"""
Fix agent communication by updating base_agent.py
This enables direct HTTP communication between local agents

Run this to patch your agents:
    python fix_agent_communication.py
"""

import os
from pathlib import Path

def fix_base_agent():
    """Update base_agent.py to use local HTTP endpoints"""
    
    base_agent_file = Path("agents/base_agent.py")
    
    if not base_agent_file.exists():
        print("❌ agents/base_agent.py not found!")
        return False
    
    print("🔧 Fixing agent communication...")
    
    # Read current content
    with open(base_agent_file, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'FIXED_COMMUNICATION' in content:
        print("✅ Already fixed!")
        return True
    
    # New send_to_peer method with local HTTP support
    new_send_to_peer = '''    async def send_to_peer(self, ctx: Context, peer_name: str, message: Model) -> bool:
        """Send message to another agent by name - FIXED_COMMUNICATION"""
        from agents.registry import registry
        
        # Get peer info from registry
        peer_info = registry.get_agent(peer_name)
        if not peer_info:
            logger.error(f"Cannot send to {peer_name} - not in registry")
            return False
        
        try:
            # Use direct HTTP endpoint instead of Agentverse resolution
            endpoint = f"http://localhost:{peer_info.port}/submit"
            
            # Send directly to local endpoint
            import aiohttp
            import json
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "sender": str(self.agent.address),
                    "target": peer_info.address,
                    "message": message.dict(),
                    "message_type": message.__class__.__name__
                }
                
                async with session.post(
                    endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"📤 Sent {message.__class__.__name__} to {peer_name}")
                        return True
                    else:
                        logger.error(f"Failed to send to {peer_name}: HTTP {resp.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send to {peer_name}: {e}")
            return False'''
    
    # Replace the old send_to_peer method
    import re
    pattern = r'async def send_to_peer\(self.*?\n        return False'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_send_to_peer, content, flags=re.DOTALL)
    else:
        print("⚠️  Could not find send_to_peer method to replace")
        return False
    
    # Backup original
    backup_file = Path("agents/base_agent.py.backup")
    with open(backup_file, 'w') as f:
        f.write(content)
    
    # Write fixed version
    with open(base_agent_file, 'w') as f:
        f.write(content)
    
    print("✅ Fixed base_agent.py")
    print(f"   Backup saved to: {backup_file}")
    return True

def create_simple_base_agent():
    """Create a completely new base_agent.py with working local communication"""
    
    print("\n🔨 Creating new base_agent.py with local communication...")
    
    new_base_agent = '''from uagents import Agent, Context, Model
from loguru import logger
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from agents.registry import register_agent, get_agent_address, registry
import aiohttp
import json

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
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            endpoint=endpoint or f"http://localhost:{port}/submit"
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
        
        logger.info(f"{name} initialized with address: {self.agent.address}")
        
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
            logger.info(f"✅ Registered {self.name} in agent registry")
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
    
    def get_peer_address(self, peer_name: str) -> Optional[str]:
        """Get another agent's address from registry"""
        address = get_agent_address(peer_name)
        if address:
            logger.debug(f"Found {peer_name} at {address[:20]}...")
        else:
            logger.warning(f"Agent {peer_name} not found in registry")
        return address
    
    async def send_to_peer(self, ctx: Context, peer_name: str, message: Model) -> bool:
        """
        Send message to another agent by name using LOCAL HTTP
        This bypasses Agentverse and uses direct HTTP communication
        """
        # Get peer info from registry (includes port)
        peer_info = registry.get_agent(peer_name)
        if not peer_info:
            logger.error(f"Cannot send to {peer_name} - not in registry")
            return False
        
        try:
            # Build local HTTP endpoint
            endpoint = f"http://localhost:{peer_info.port}/submit"
            
            logger.debug(f"Sending to {peer_name} at {endpoint}")
            
            # Create payload
            payload = {
                "sender": str(self.agent.address),
                "target": peer_info.address,
                "message": message.dict(),
                "message_type": message.__class__.__name__,
                "schema_digest": message.schema_digest if hasattr(message, 'schema_digest') else ""
            }
            
            # Send via HTTP POST
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    
                    if resp.status == 200:
                        logger.info(f"📤 Sent {message.__class__.__name__} to {peer_name}")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"HTTP {resp.status} from {peer_name}: {text[:100]}")
                        return False
            
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Cannot connect to {peer_name} at port {peer_info.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send to {peer_name}: {type(e).__name__}: {e}")
            return False
    
    def get_agent(self):
        return self.agent
    
    def get_address(self):
        return self.agent.address
'''
    
    # Backup existing file
    base_agent_file = Path("agents/base_agent.py")
    if base_agent_file.exists():
        backup_file = Path("agents/base_agent.py.backup2")
        with open(base_agent_file, 'r') as f:
            with open(backup_file, 'w') as bf:
                bf.write(f.read())
        print(f"✅ Backed up original to {backup_file}")
    
    # Write new version
    with open(base_agent_file, 'w') as f:
        f.write(new_base_agent)
    
    print("✅ Created new base_agent.py with local HTTP communication")
    return True

def main():
    print("="*70)
    print("🔧 FIXING AGENT COMMUNICATION")
    print("="*70)
    print("\nThis will enable direct HTTP communication between local agents")
    print("instead of trying to go through Agentverse.\n")
    
    # Option: Create clean new version
    if create_simple_base_agent():
        print("\n" + "="*70)
        print("✅ AGENT COMMUNICATION FIXED!")
        print("="*70)
        print("\nNow restart your test:")
        print("  1. Kill any running agents (Ctrl+C)")
        print("  2. Run: ./setup_e2e_test_fixed.sh")
        print("\nAgents will now communicate directly via HTTP")
        print("="*70)
    else:
        print("\n❌ Fix failed. Manual intervention needed.")
        print("\nPlease check agents/base_agent.py")

if __name__ == "__main__":
    main()