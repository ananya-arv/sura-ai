from typing import Dict
from dataclasses import dataclass

@dataclass
class AgentInfo:
    name: str
    address: str
    port: int
    capabilities: list[str]

class AgentRegistry:
    """Central registry for all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
    
    def register(self, name: str, address: str, port: int, capabilities: list[str]):
        self.agents[name] = AgentInfo(name, address, port, capabilities)
        print(f"✅ Registered agent: {name} at {address}")
    
    def get_agent(self, name: str) -> AgentInfo:
        return self.agents.get(name)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        return self.agents
    
    def get_agents_by_capability(self, capability: str) -> list[AgentInfo]:
        return [agent for agent in self.agents.values() if capability in agent.capabilities]

# Global registry
registry = AgentRegistry()
