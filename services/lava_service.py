"""
Lava AI Service for SuraAI - Claude Sonnet 3.5 through Lava's API
CORRECTED VERSION with proper fallback and error handling
"""

import os
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger
import json

class LavaAIService:
    """Integration with Lava Gateway - Claude through Lava's infrastructure"""
    
    def __init__(self):
        # Lava configuration
        self.lava_base_url = "https://api.lavapayments.com/v1"
        self.forward_token = os.getenv("LAVA_FORWARD_TOKEN")  # Changed to match intelligent_response_agent
        
        # Use Lava's Claude endpoint
        self.model = "claude-sonnet-3-5-20241022"
        
        # Construct Lava's chat completions URL
        self.lava_url = f"{self.lava_base_url}/forward?u=https://api.anthropic.com/v1/messages"
        
        # Check if Lava is available
        self.available = bool(self.forward_token)
        
        if self.available:
            logger.info(f"🌊 Lava AI Service initialized")
            logger.info(f"   Model: {self.model}")
            logger.info(f"   Using Lava credits (no separate API key needed!)")
        else:
            logger.warning("⚠️  LAVA_FORWARD_TOKEN not set - AI features disabled")
            logger.info("   System will use rule-based decisions (still works!)")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Lava connection - ONLY used in test script"""
        if not self.available:
            return {"test_request": "SKIPPED", "reason": "No Lava token"}
        
        try:
            test_data = {
                "alert_id": "TEST-CONNECTION",
                "severity": "LOW",
                "system_id": "test",
                "metric_type": "CPU",
                "current_value": 50.0,
                "expected_value": 40.0,
                "confidence": 0.8
            }
            
            result = await self.analyze_incident(test_data)
            return {
                "test_request": "SUCCESS",
                "lava_request_id": result.get("lava_request_id", "N/A")
            }
        except Exception as e:
            return {"test_request": "FAILED", "error": str(e)}
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incident using Claude Sonnet 3.5 through Lava
        
        Returns dict with:
        - recommendation: str
        - confidence: float
        - reasoning: str
        - severity: str
        - lava_request_id: str (for tracking)
        - ai_provider: str
        """
        if not self.available:
            logger.warning("Lava not available, using fallback")
            return self._fallback_response()
        
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.forward_token}",
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
                
                logger.debug(f"🌊 Sending request to Lava...")
                
                async with session.post(
                    self.lava_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Lava error ({resp.status}): {error_text}")
                        return self._fallback_response()
                    
                    # Get Lava request ID for tracking
                    lava_request_id = resp.headers.get('x-lava-request-id', 'unknown')
                    
                    response_data = await resp.json()
                    
                    # Extract Claude's response (OpenAI format)
                    content = response_data['choices'][0]['message']['content']
                    
                    # Parse JSON from Claude's response
                    try:
                        analysis = json.loads(content)
                        
                        # Add Lava metadata
                        analysis['lava_request_id'] = lava_request_id
                        analysis['ai_provider'] = 'Claude Sonnet 3.5 (via Lava)'
                        
                        # Ensure required fields exist
                        if 'recommendation' not in analysis:
                            analysis['recommendation'] = 'INVESTIGATE'
                        if 'confidence' not in analysis:
                            analysis['confidence'] = 0.7
                        if 'reasoning' not in analysis:
                            analysis['reasoning'] = 'AI analysis completed'
                        
                        logger.info(f"✅ Lava Request ID: {lava_request_id}")
                        logger.debug(f"🧠 Claude recommendation: {analysis.get('recommendation')}")
                        
                        return analysis
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Claude response not valid JSON: {e}")
                        logger.debug(f"Raw content: {content[:200]}")
                        return self._parse_natural_language_response(content, lava_request_id)
            
        except aiohttp.ClientError as e:
            logger.error(f"Lava connection error: {e}")
            return self._fallback_response()
        except asyncio.TimeoutError:
            logger.error("Lava request timed out")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"Unexpected error in Lava analysis: {e}")
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

Respond with this exact JSON structure (no markdown, no extra text):
{{
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "root_cause": "brief description",
    "recommendation": "ROLLBACK|FAILOVER|SCALE_UP|ISOLATE|INVESTIGATE",
    "confidence": 0.75,
    "reasoning": "one sentence explanation"
}}

Be decisive. Production systems depend on fast, accurate decisions."""
    
    def _parse_natural_language_response(self, content: str, lava_request_id: str) -> Dict[str, Any]:
        """Parse natural language response if JSON parsing fails"""
        logger.info("Parsing natural language response from Claude...")
        
        recommendation = "INVESTIGATE"
        content_lower = content.lower()
        
        if "rollback" in content_lower:
            recommendation = "ROLLBACK"
        elif "scale" in content_lower or "scale_up" in content_lower:
            recommendation = "SCALE_UP"
        elif "isolate" in content_lower:
            recommendation = "ISOLATE"
        elif "failover" in content_lower:
            recommendation = "FAILOVER"
        
        return {
            "recommendation": recommendation,
            "confidence": 0.7,
            "reasoning": content[:150] if len(content) > 150 else content,
            "severity": "MEDIUM",
            "lava_request_id": lava_request_id,
            "ai_provider": "Claude Sonnet 3.5 (via Lava, parsed)"
        }
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response when Lava/Claude fails"""
        return {
            "recommendation": "INVESTIGATE",
            "confidence": 0.0,
            "reasoning": "AI analysis unavailable - using fallback",
            "severity": "MEDIUM",
            "lava_request_id": "",
            "ai_provider": "Fallback (rule-based)"
        }
    
    async def predict_failure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict failures using Claude through Lava"""
        if not self.available:
            return {"failure_probability": 0.0, "failure_type": "NONE"}
        
        prompt = f"""Analyze system metrics and predict potential failures. Respond with JSON only.

Metrics:
- CPU: {metrics.get('cpu_usage', 0):.1f}%
- Memory: {metrics.get('memory_usage', 0):.1f}%
- Disk: {metrics.get('disk_usage', 0):.1f}%
- Network Latency: {metrics.get('network_latency', 0):.1f}ms
- Error Count: {metrics.get('error_count', 0)}

JSON Response (no markdown):
{{
    "failure_probability": 0.5,
    "failure_type": "MEMORY_LEAK",
    "time_to_failure_minutes": 30,
    "preventive_action": "RESTART",
    "confidence": 0.8
}}"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.forward_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a predictive SRE AI. Output JSON only."},
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
                        
                        try:
                            return json.loads(content)
                        except:
                            # Fallback parsing
                            return {
                                "failure_probability": 0.5,
                                "failure_type": "UNKNOWN",
                                "preventive_action": "INVESTIGATE"
                            }
                    
                    return {"failure_probability": 0.0, "failure_type": "NONE"}
        
        except Exception as e:
            logger.error(f"Failure prediction failed: {e}")
            return {"failure_probability": 0.0, "failure_type": "NONE"}

# Global instance
lava_service = LavaAIService()