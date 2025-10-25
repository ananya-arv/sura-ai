"""
Lava AI Service for SuraAI - Claude Sonnet 3.5 through Lava's API
No separate Anthropic key needed - uses Lava credits!
"""

import os
import aiohttp
from typing import Dict, Any
from loguru import logger
import json

class LavaAIService:
    """Integration with Lava Gateway - Claude through Lava's infrastructure"""
    
    def __init__(self):
        # Lava configuration
        self.lava_base_url = "https://api.lavapayments.com/v1"
        self.lava_token = os.getenv("LAVA_FORWARD_TOKEN")
        
        # Use Lava's Claude endpoint (NOT Anthropic direct!)
        self.model = "claude-sonnet-3-5-20241022"
        
        # Construct Lava's chat completions URL
        # This uses Lava's credits, not separate API keys!
        self.lava_url = f"{self.lava_base_url}/chat/completions"
        
        logger.info(f"🌊 Lava AI Service initialized")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   Using Lava credits (no separate API key needed!)")
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incident using Claude Sonnet 3.5 through Lava
        
        Benefits:
        - Uses your $10 Lava credit!
        - Automatic cost tracking
        - No separate Anthropic account needed
        """
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    # Only Lava token needed!
                    "Authorization": f"Bearer {self.lava_token}",
                    "Content-Type": "application/json"
                }
                
                # OpenAI-style format (Lava handles Claude conversion)
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert SRE AI. Respond with JSON only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024
                }
                
                logger.debug(f"🌊 Sending request to Lava (using your credits)...")
                
                async with session.post(
                    self.lava_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Lava error: {error_text}")
                        return self._fallback_response()
                    
                    # Get Lava request ID for tracking
                    lava_request_id = resp.headers.get('x-lava-request-id')
                    logger.info(f"✅ Lava Request ID: {lava_request_id}")
                    
                    response_data = await resp.json()
                    
                    # Extract Claude's response (OpenAI format)
                    content = response_data['choices'][0]['message']['content']
                    
                    # Parse JSON from Claude's response
                    try:
                        analysis = json.loads(content)
                        logger.info(f"🧠 Claude analysis complete (via Lava credits)")
                        logger.info(f"   Recommendation: {analysis.get('recommendation')}")
                        logger.info(f"   Confidence: {analysis.get('confidence', 0):.2f}")
                        logger.info(f"💰 Cost deducted from Lava wallet")
                        
                        return analysis
                    except json.JSONDecodeError:
                        logger.warning("Claude response not in JSON format, parsing...")
                        return self._parse_natural_language_response(content)
            
        except Exception as e:
            logger.error(f"Lava/Claude analysis failed: {e}")
            return self._fallback_response()
    
    def _build_incident_prompt(self, incident_data: Dict[str, Any]) -> str:
        """Build optimized prompt for Claude via Lava"""
        return f"""Analyze this production incident and respond ONLY with valid JSON.

Incident Data:
- Alert ID: {incident_data.get('alert_id')}
- Severity: {incident_data.get('severity')}
- System: {incident_data.get('system_id')}
- Metric: {incident_data.get('metric_type')}
- Current Value: {incident_data.get('current_value')}
- Expected Value: {incident_data.get('expected_value')}
- Confidence: {incident_data.get('confidence', 0):.2f}

Respond with this exact JSON structure:
{{
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "root_cause": "brief description",
    "recommendation": "ROLLBACK|FAILOVER|SCALE_UP|ISOLATE|INVESTIGATE|IGNORE",
    "confidence": 0.0-1.0,
    "reasoning": "one sentence explanation",
    "estimated_impact": "user impact estimate",
    "urgency_score": 1-10
}}

Be decisive. Production systems depend on fast, accurate decisions."""
    
    def _parse_natural_language_response(self, content: str) -> Dict[str, Any]:
        """Parse natural language response if JSON parsing fails"""
        recommendation = "INVESTIGATE"
        if "rollback" in content.lower():
            recommendation = "ROLLBACK"
        elif "scale" in content.lower():
            recommendation = "SCALE_UP"
        elif "isolate" in content.lower():
            recommendation = "ISOLATE"
        
        return {
            "recommendation": recommendation,
            "confidence": 0.7,
            "reasoning": content[:100],
            "severity": "MEDIUM"
        }
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response when Lava/Claude fails"""
        return {
            "recommendation": "MANUAL_REVIEW",
            "confidence": 0.0,
            "reasoning": "AI analysis unavailable - Lava connection failed",
            "severity": "HIGH"
        }
    
    async def predict_failure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict failures using Claude through Lava"""
        prompt = f"""Analyze system metrics and predict potential failures. Respond with JSON only.

Metrics:
- CPU: {metrics.get('cpu_usage', 0):.1f}%
- Memory: {metrics.get('memory_usage', 0):.1f}%
- Disk: {metrics.get('disk_usage', 0):.1f}%
- Network Latency: {metrics.get('network_latency', 0):.1f}ms
- Error Count: {metrics.get('error_count', 0)}

JSON Response:
{{
    "failure_probability": 0.0-1.0,
    "failure_type": "MEMORY_LEAK|CPU_SPIKE|DISK_FULL|NETWORK_ISSUE|NONE",
    "time_to_failure_minutes": int,
    "preventive_action": "SCALE_UP|RESTART|INVESTIGATE|NONE",
    "confidence": 0.0-1.0
}}"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.lava_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a predictive SRE AI."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 512
                }
                
                async with session.post(
                    self.lava_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        return json.loads(content)
                    
                    return {"failure_probability": 0.0, "failure_type": "NONE"}
        
        except Exception as e:
            logger.error(f"Failure prediction failed: {e}")
            return {"failure_probability": 0.0, "failure_type": "NONE"}

# Global instance
lava_service = LavaAIService()
