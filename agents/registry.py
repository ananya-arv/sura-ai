from typing import Dict, Optional, List
from dataclasses import dataclass, field
import json
import os
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path

@dataclass
class AgentInfo:
    name: str
    address: str
    port: int
    capabilities: List[str]
    status: str = "active"
    last_seen: float = 0.0

class AgentRegistry:
    """
    Central registry for agent discovery and communication
    Supports both in-memory and file-based persistence
    """
    
    def __init__(self, registry_file: str = "agent_registry.json"):
        self.agents: Dict[str, AgentInfo] = {}
        self.registry_file = registry_file
        self.load_registry()
    
    def register(self, name: str, address: str, port: int, capabilities: List[str]) -> None:
        """Register an agent in the system"""
        self.agents[name] = AgentInfo(
            name=name,
            address=address,
            port=port,
            capabilities=capabilities
        )
        logger.info(f"✅ Registered: {name} at {address[:20]}... (port {port})")
        self.save_registry()
    
    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get agent info by name"""
        return self.agents.get(name)
    
    def get_agent_address(self, name: str) -> Optional[str]:
        """Get agent address by name (convenience method)"""
        agent = self.get_agent(name)
        return agent.address if agent else None
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get all registered agents"""
        return self.agents
    
    def get_agents_by_capability(self, capability: str) -> List[AgentInfo]:
        """Find agents with specific capability"""
        return [
            agent for agent in self.agents.values() 
            if capability in agent.capabilities
        ]
    
    def save_registry(self) -> None:
        """Persist registry to file"""
        try:
            data = {
                name: {
                    "name": info.name,
                    "address": info.address,
                    "port": info.port,
                    "capabilities": info.capabilities,
                    "status": info.status
                }
                for name, info in self.agents.items()
            }
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def load_registry(self) -> None:
        """Load registry from file"""
        if not os.path.exists(self.registry_file):
            logger.info("No existing registry found, starting fresh")
            return
        
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            
            for name, info in data.items():
                self.agents[name] = AgentInfo(**info)
            
            logger.info(f"✅ Loaded {len(self.agents)} agents from registry")
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
    
    def clear_registry(self) -> None:
        """Clear all registered agents"""
        self.agents.clear()
        self.save_registry()
        logger.info("🗑️  Registry cleared")
    
    def print_registry(self) -> None:
        """Print all registered agents"""
        print("\n" + "="*70)
        print("📋 AGENT REGISTRY")
        print("="*70)
        
        if not self.agents:
            print("No agents registered")
            return
        
        for name, info in self.agents.items():
            print(f"\n🤖 {name.upper()}")
            print(f"   Address: {info.address}")
            print(f"   Port: {info.port}")
            print(f"   Capabilities: {', '.join(info.capabilities)}")
            print(f"   Status: {info.status}")
        
        print("\n" + "="*70)

# Global registry instance
registry = AgentRegistry()

# Convenience functions for agents to use
def register_agent(name: str, address: str, port: int, capabilities: List[str]) -> None:
    """Register this agent in the global registry"""
    registry.register(name, address, port, capabilities)

def get_agent_address(name: str) -> Optional[str]:
    """Get another agent's address"""
    return registry.get_agent_address(name)

def discover_agents(capability: str) -> List[str]:
    """Find all agents with a specific capability"""
    agents = registry.get_agents_by_capability(capability)
    return [agent.address for agent in agents]