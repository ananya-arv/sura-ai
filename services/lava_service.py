import aiohttp
import os
from typing import Dict, Any, Optional
from loguru import logger
import json

class LavaAIService:
    """Integration with Lava AI for intelligent decision-making"""
    
    def __init__(self):
        self.api_key = os.getenv("LAVA_API_KEY")
        self.endpoint = os.getenv("LAVA_ENDPOINT", "https://api.lavanet.xyz")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze incident and recommend actions"""
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            response = await self._call_lava(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"Lava AI call failed: {e}")
            return {"recommendation": "MANUAL_REVIEW", "confidence": 0.0}
    
    async def predict_failure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict potential failures from metrics"""
        prompt = f"""Analyze these system metrics and predict potential failures:

Metrics: {json.dumps(metrics, indent=2)}

Provide:
1. Failure probability (0-1)
2. Most likely failure type
3. Recommended preventive actions
4. Time to failure estimate

Respond in JSON format."""

        try:
            response = await self._call_lava(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"failure_probability": 0.0}
    
    async def generate_runbook(self, incident_type: str, context: str) -> str:
        """Generate custom runbook for incident"""
        prompt = f"""Generate a step-by-step runbook for this incident:

Type: {incident_type}
Context: {context}

Provide detailed steps for automated remediation."""

        try:
            response = await self._call_lava(prompt)
            return response
        except Exception as e:
            logger.error(f"Runbook generation failed: {e}")
            return "Manual intervention required"
    
    def _build_incident_prompt(self, incident_data: Dict[str, Any]) -> str:
        """Build prompt for incident analysis"""
        return f"""You are an expert SRE AI analyzing a production incident.

Incident Data:
{json.dumps(incident_data, indent=2)}

Provide analysis in JSON format with:
1. severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
2. root_cause: string
3. recommendation: "ROLLBACK" | "FAILOVER" | "SCALE" | "INVESTIGATE" | "IGNORE"
4. confidence: float (0-1)
5. reasoning: string
6. estimated_impact: string

Respond ONLY with valid JSON."""
    
    async def _call_lava(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to Lava AI"""
        if not self.session:
            await self.initialize()
        
        payload = {
            "model": "gpt-4",  # Adjust based on Lava's model names
            "messages": [
                {"role": "system", "content": "You are an expert SRE AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        async with self.session.post(f"{self.endpoint}/chat/completions", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Lava API error: {resp.status}")
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            return {"recommendation": "MANUAL_REVIEW", "confidence": 0.0}

# Global instance
lava_service = LavaAIService()
