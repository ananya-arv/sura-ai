"""
Lava AI Service for SuraAI - Claude Sonnet 3.5 through Lava's API
FIXED VERSION - Proper token detection
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
        
        # Model configuration
        self.model = "claude-sonnet-3-5-20241022"
        
        # Lava endpoint (uses Anthropic's format)
        self.lava_url = f"{self.lava_base_url}/forward?u=https://api.anthropic.com/v1/messages"
        
        # Check if Lava is available
        self.available = bool(self.lava_token)
        
        if self.available:
            logger.info(f"🌊 Lava AI Service initialized")
            logger.info(f"   Model: {self.model}")
            logger.info(f"   Token: {self.lava_token[:15]}...")
            logger.info(f"   Endpoint: {self.lava_url}")
            logger.info(f"   ✅ LAVA IS ENABLED")
        else:
            logger.warning("⚠️  LAVA_FORWARD_TOKEN not set - AI features disabled")
            logger.info("   System will use rule-based decisions")
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incident using Claude Sonnet 3.5 through Lava
        """
        if not self.available:
            logger.warning("❌ Lava not available - no token!")
            return self._fallback_response()
        
        prompt = self._build_incident_prompt(incident_data)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.lava_token}",
                    "Content-Type": "application/json"
                }
                
                # OpenAI-compatible format
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert SRE AI. Respond ONLY with valid JSON. No markdown, no code blocks, just pure JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024
                }
                
                logger.info(f"🌊 Sending request to Lava...")
                logger.debug(f"   URL: {self.lava_url}")
                logger.debug(f"   Model: {self.model}")
                
                async with session.post(
                    self.lava_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    
                    response_text = await resp.text()
                    
                    if resp.status != 200:
                        logger.error(f"❌ Lava error ({resp.status})")
                        logger.error(f"   Response: {response_text[:200]}")
                        return self._fallback_response()
                    
                    # Get Lava request ID
                    lava_request_id = resp.headers.get('x-lava-request-id', 'unknown')
                    logger.info(f"✅ Lava Request ID: {lava_request_id}")
                    
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Lava response as JSON: {e}")
                        logger.error(f"Raw response: {response_text[:500]}")
                        return self._fallback_response()
                    
                    # Extract Claude's response
                    try:
                        content = response_data['choices'][0]['message']['content']
                        logger.debug(f"Claude response: {content[:200]}")
                    except (KeyError, IndexError) as e:
                        logger.error(f"Unexpected response format: {e}")
                        logger.error(f"Response data: {response_data}")
                        return self._fallback_response()
                    
                    # Parse Claude's JSON response
                    try:
                        # Remove markdown code blocks if present
                        if content.startswith('```'):
                            content = content.split('```')[1]
                            if content.startswith('json'):
                                content = content[4:]
                        
                        analysis = json.loads(content.strip())
                        
                        # Add metadata
                        analysis['lava_request_id'] = lava_request_id
                        analysis['ai_provider'] = 'Claude Sonnet 3.5 (via Lava)'
                        
                        # Ensure required fields
                        if 'recommendation' not in analysis:
                            analysis['recommendation'] = 'INVESTIGATE'
                        if 'confidence' not in analysis:
                            analysis['confidence'] = 0.75
                        if 'reasoning' not in analysis:
                            analysis['reasoning'] = 'AI analysis completed'
                        
                        logger.info(f"✅ Claude analysis successful!")
                        logger.info(f"   Recommendation: {analysis.get('recommendation')}")
                        logger.info(f"   Confidence: {analysis.get('confidence'):.2f}")
                        
                        return analysis
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Claude response not valid JSON: {e}")
                        logger.warning(f"Content: {content[:300]}")
                        return self._parse_natural_language_response(content, lava_request_id)
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ Lava connection error: {e}")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
            return self._fallback_response()
    
    def _build_incident_prompt(self, incident_data: Dict[str, Any]) -> str:
        """Build optimized prompt for Claude via Lava"""
        return f"""Analyze this production incident and respond ONLY with valid JSON (no markdown formatting).

Incident Data:
- Alert ID: {incident_data.get('alert_id')}
- Severity: {incident_data.get('severity')}
- System: {incident_data.get('system_id')}
- Metric: {incident_data.get('metric_type')}
- Current Value: {incident_data.get('current_value')}
- Expected Value: {incident_data.get('expected_value')}
- Confidence: {incident_data.get('confidence', 0):.2f}

Respond with ONLY this JSON (no code blocks, no markdown):
{{
    "severity": "HIGH",
    "root_cause": "brief description",
    "recommendation": "ROLLBACK",
    "confidence": 0.85,
    "reasoning": "one sentence explanation"
}}

Choose recommendation from: ROLLBACK, FAILOVER, SCALE_UP, ISOLATE, INVESTIGATE, RESTART"""
    
    def _parse_natural_language_response(self, content: str, lava_request_id: str) -> Dict[str, Any]:
        """Parse natural language response if JSON parsing fails"""
        logger.info("📝 Parsing natural language response...")
        
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
        elif "restart" in content_lower:
            recommendation = "RESTART"
        
        return {
            "recommendation": recommendation,
            "confidence": 0.7,
            "reasoning": content[:150] if len(content) > 150 else content,
            "severity": "MEDIUM",
            "lava_request_id": lava_request_id,
            "ai_provider": "Claude Sonnet 3.5 (via Lava, parsed)"
        }
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response when Lava fails"""
        return {
            "recommendation": "INVESTIGATE",
            "confidence": 0.0,
            "reasoning": "AI analysis unavailable",
            "severity": "MEDIUM",
            "lava_request_id": "",
            "ai_provider": "Fallback (rule-based)"
        }

# Global instance
lava_service = LavaAIService()