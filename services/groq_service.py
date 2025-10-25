"""
Groq AI Service for SuraAI - Ultra-fast LLM inference for real-time decisions
Replace Lava AI with this for sub-second incident analysis
"""

import os
from groq import Groq
from typing import Dict, Any, Optional
from loguru import logger
import json

class GroqAIService:
    """Integration with Groq for ultra-fast incident analysis"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        # Use fastest model for real-time decisions
        self.model = "llama-3.1-70b-versatile"  # Fast + accurate
        # Alternative: "mixtral-8x7b-32768" for even faster responses
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ultra-fast incident analysis using Groq's LPU
        Returns decision in <500ms vs 2-3s with other providers
        """
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            # Groq's LPU provides near-instant inference
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SRE AI analyzing production incidents. Respond ONLY with valid JSON. Be fast and decisive."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1,  # Low temp for consistent decisions
                max_tokens=500,
                top_p=0.9,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"🚀 Groq analysis completed in {response.usage.total_time:.3f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return {
                "recommendation": "MANUAL_REVIEW",
                "confidence": 0.0,
                "reasoning": "AI analysis unavailable"
            }
    
    async def predict_failure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict potential failures from system metrics"""
        prompt = f"""Analyze these system metrics and predict potential failures:

CPU: {metrics.get('cpu_usage', 0):.1f}%
Memory: {metrics.get('memory_usage', 0):.1f}%
Disk: {metrics.get('disk_usage', 0):.1f}%
Network Latency: {metrics.get('network_latency', 0):.1f}ms
Error Count: {metrics.get('error_count', 0)}

Respond with JSON:
{{
    "failure_probability": 0.0-1.0,
    "failure_type": "MEMORY_LEAK|CPU_SPIKE|DISK_FULL|NETWORK_ISSUE|NONE",
    "time_to_failure_minutes": int,
    "preventive_action": "SCALE_UP|RESTART|INVESTIGATE|NONE",
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a predictive SRE AI."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            prediction = json.loads(response.choices[0].message.content)
            return prediction
            
        except Exception as e:
            logger.error(f"Failure prediction failed: {e}")
            return {"failure_probability": 0.0, "failure_type": "NONE"}
    
    async def generate_runbook(self, incident_type: str, context: str) -> str:
        """Generate step-by-step recovery runbook"""
        prompt = f"""Generate a concise runbook for automated remediation:

Incident Type: {incident_type}
Context: {context}

Provide 3-5 actionable steps for autonomous execution.
Be specific and technical."""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert SRE creating automated runbooks."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Runbook generation failed: {e}")
            return "1. Isolate affected systems\n2. Collect logs\n3. Manual intervention required"
    
    def analyze_incident_sync(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version for non-async contexts"""
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert SRE AI. Respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return {"recommendation": "MANUAL_REVIEW", "confidence": 0.0}
    
    def _build_incident_prompt(self, incident_data: Dict[str, Any]) -> str:
        """Build optimized prompt for incident analysis"""
        return f"""Analyze this production incident and recommend action:

Alert ID: {incident_data.get('alert_id')}
Severity: {incident_data.get('severity')}
System: {incident_data.get('system_id')}
Metric: {incident_data.get('metric_type')}
Current Value: {incident_data.get('current_value')}
Expected Value: {incident_data.get('expected_value')}
Detection Confidence: {incident_data.get('confidence', 0):.2f}

Respond with JSON:
{{
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "root_cause": "brief description",
    "recommendation": "ROLLBACK|FAILOVER|SCALE|ISOLATE|INVESTIGATE|IGNORE",
    "confidence": 0.0-1.0,
    "reasoning": "one sentence why",
    "estimated_impact": "user impact estimate",
    "urgency_score": 1-10
}}

Be decisive. Lives depend on fast decisions."""

# Global instance
groq_service = GroqAIService()
