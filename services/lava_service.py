"""
Lava AI Service for SuraAI - Claude Sonnet 3.5 through Lava's API
FIXED VERSION - Correct model and Anthropic response format
"""

import os
import aiohttp
from typing import Dict, Any
from loguru import logger
import json
from dotenv import load_dotenv
load_dotenv()

class LavaAIService:
    """Integration with Lava Gateway - Claude through Lava's infrastructure"""
    
    def __init__(self):
        # Lava configuration
        self.lava_base_url = "https://api.lavapayments.com/v1"
        self.lava_token = os.getenv("LAVA_FORWARD_TOKEN")
        
        # Model configuration - FIXED: Use Lava-supported model
        self.model = "claude-3-5-sonnet-20240620"
        
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
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"  # Required for Anthropic API
                }
                
                # Anthropic message format
                payload = {
                    "model": self.model,
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"You are an expert SRE AI. Respond ONLY with valid JSON. No markdown, no code blocks, just pure JSON.\n\n{prompt}"
                        }
                    ]
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
                    
                    # Get Lava request ID from headers
                    lava_request_id = resp.headers.get('x-lava-request-id', '')
                    if lava_request_id:
                        logger.info(f"✅ Lava Request ID: {lava_request_id}")
                    else:
                        logger.warning(f"⚠️  No x-lava-request-id header found")
                    
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Lava response as JSON: {e}")
                        logger.error(f"Raw response: {response_text[:500]}")
                        return self._fallback_response()
                    
                    # FIXED: Extract Claude's response using Anthropic format
                    try:
                        # Anthropic returns: {"content": [{"type": "text", "text": "..."}], "role": "assistant"}
                        if 'content' in response_data and isinstance(response_data['content'], list):
                            # Get text from first content block
                            content = response_data['content'][0]['text']
                            logger.debug(f"Claude response: {content[:200]}")
                        else:
                            logger.error(f"Unexpected Anthropic response structure")
                            logger.error(f"Response keys: {response_data.keys()}")
                            return self._fallback_response()
                        
                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"Failed to extract content: {e}")
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
            import traceback
            traceback.print_exc()
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
    
    async def analyze_canary_deployment(self, deployment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized analysis for canary deployment decisions
        """
        if not self.available:
            return self._fallback_response()
        
        context = deployment_data.get('additional_context', {})
        
        prompt = f"""You are an expert SRE AI analyzing canary deployment test results.

    Deployment Information:
    - Update ID: {context.get('update_id')}
    - Version: {context.get('version')}
    - Description: {context.get('description')}

    Canary Test Results:
    - Systems Tested: {context.get('canary_systems')} out of {context.get('total_systems')} total
    - Test Duration: {context.get('test_duration')} seconds
    - Errors Detected: {context.get('errors')}
    - Warnings: {context.get('warnings')}
    - Error Rate: {context.get('error_rate')}
    - Warning Rate: {context.get('warning_rate')}
    - Latency Impact: {context.get('latency_impact')}

    Based on these canary test results, what should we do?

    Respond with ONLY valid JSON (no markdown):
    {{
        "recommendation": "DEPLOY|INVESTIGATE|ROLLBACK",
        "confidence": 0.85,
        "reasoning": "brief explanation of your decision",
        "severity": "LOW|MEDIUM|HIGH|CRITICAL"
    }}

    Guidelines:
    - ROLLBACK: Clear evidence of failures (>3% error rate or critical errors)
    - INVESTIGATE: Warning signs but not critical (1-3% errors, or elevated warnings)
    - DEPLOY: All metrics look good (<1% errors, no warnings)"""
        
        # Use the same analyze_incident flow
        deployment_data['metric_type'] = 'CANARY_TEST'
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.lava_token}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                
                payload = {
                    "model": self.model,
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"You are an expert SRE AI. Respond ONLY with valid JSON. No markdown, no code blocks.\n\n{prompt}"
                        }
                    ]
                }
                
                async with session.post(
                    self.lava_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    
                    if resp.status != 200:
                        response_text = await resp.text()
                        logger.error(f"Lava error ({resp.status}): {response_text[:200]}")
                        return self._fallback_response()
                    
                    lava_request_id = resp.headers.get('x-lava-request-id', '')
                    response_data = await resp.json()
                    content = response_data['content'][0]['text']
                    
                    # Parse JSON response
                    if content.startswith('```'):
                        content = content.split('```')[1]
                        if content.startswith('json'):
                            content = content[4:]
                    
                    analysis = json.loads(content.strip())
                    analysis['lava_request_id'] = lava_request_id
                    analysis['ai_provider'] = 'Claude Sonnet 3.5 (via Lava)'
                    
                    return analysis
                    
        except Exception as e:
            logger.error(f"Canary AI analysis failed: {e}")
            return self._fallback_response()

# Global instance
lava_service = LavaAIService()