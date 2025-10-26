#!/usr/bin/env python3
"""
Debug Lava API Request
Make a direct test request to see what's failing
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

async def test_lava_direct():
    """Make a direct test request to Lava API"""
    
    load_dotenv()
    token = os.getenv("LAVA_FORWARD_TOKEN")
    
    print("="*70)
    print("🧪 TESTING LAVA API DIRECTLY")
    print("="*70)
    
    if not token:
        print("\n❌ No LAVA_FORWARD_TOKEN found!")
        return
    
    print(f"\n✅ Token found: {token[:20]}...")
    print(f"   Length: {len(token)} chars")
    
    # Lava endpoint
    url = "https://api.lavapayments.com/v1/forward?u=https://api.anthropic.com/v1/messages"
    
    # Test payload (same as your agent uses)
    payload = {
        "model": "claude-sonnet-3-5-20241022",
        "messages": [
            {
                "role": "system",
                "content": "You are a test assistant. Respond with just 'OK'."
            },
            {
                "role": "user",
                "content": "Say OK"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 Sending request to Lava...")
    print(f"   URL: {url}")
    print(f"   Model: {payload['model']}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                
                status = resp.status
                response_text = await resp.text()
                
                print(f"\n📥 Response:")
                print(f"   Status: {status}")
                print(f"   Headers:")
                for key, value in resp.headers.items():
                    if 'lava' in key.lower():
                        print(f"      {key}: {value}")
                
                print(f"\n   Body (first 500 chars):")
                print(f"   {response_text[:500]}")
                
                if status == 200:
                    try:
                        data = json.loads(response_text)
                        print(f"\n✅ SUCCESS!")
                        
                        # Check for lava_request_id
                        lava_id = resp.headers.get('x-lava-request-id')
                        if lava_id:
                            print(f"   🎯 Lava Request ID: {lava_id}")
                        else:
                            print(f"   ⚠️  No x-lava-request-id header found!")
                        
                        # Show response structure
                        print(f"\n   Response structure:")
                        print(f"   Keys: {list(data.keys())}")
                        
                        if 'choices' in data:
                            print(f"   ✅ Has 'choices' key (OpenAI format)")
                            if data['choices']:
                                msg = data['choices'][0].get('message', {})
                                content = msg.get('content', '')
                                print(f"   Content: {content[:100]}")
                        else:
                            print(f"   ⚠️  Unexpected response format!")
                            print(f"   Full response: {json.dumps(data, indent=2)[:500]}")
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        print(f"\n❌ Response is not valid JSON: {e}")
                        return False
                
                elif status == 401:
                    print(f"\n❌ AUTHENTICATION FAILED")
                    print(f"   Your token is invalid or expired")
                    print(f"   Get a new token from: https://lavapayments.com/dashboard/build/secret-keys")
                    return False
                
                elif status == 402:
                    print(f"\n❌ PAYMENT REQUIRED")
                    print(f"   Your Lava wallet has insufficient funds")
                    print(f"   Add funds at: https://lavapayments.com/dashboard/wallet/billing")
                    return False
                
                elif status == 403:
                    print(f"\n❌ FORBIDDEN")
                    print(f"   Token doesn't have permission for this endpoint")
                    return False
                
                elif status >= 500:
                    print(f"\n❌ SERVER ERROR")
                    print(f"   Lava's API is having issues")
                    print(f"   Try again in a few minutes")
                    return False
                
                else:
                    print(f"\n❌ UNEXPECTED ERROR")
                    print(f"   Status code: {status}")
                    
                    try:
                        error_data = json.loads(response_text)
                        print(f"   Error: {json.dumps(error_data, indent=2)}")
                    except:
                        pass
                    
                    return False
    
    except aiohttp.ClientConnectorError as e:
        print(f"\n❌ CONNECTION ERROR")
        print(f"   Cannot reach Lava API: {e}")
        print(f"   Check your internet connection")
        return False
    
    except asyncio.TimeoutError:
        print(f"\n❌ TIMEOUT")
        print(f"   Request took longer than 30 seconds")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_format():
    """Check if token format is correct"""
    
    load_dotenv()
    token = os.getenv("LAVA_FORWARD_TOKEN")
    
    print("\n" + "="*70)
    print("🔍 TOKEN FORMAT CHECK")
    print("="*70)
    
    if not token:
        print("\n❌ No token!")
        return False
    
    print(f"\n📋 Token Info:")
    print(f"   Length: {len(token)} chars")
    print(f"   First 20: {token[:20]}...")
    print(f"   Last 20: ...{token[-20:]}")
    
    # JWT tokens are base64 encoded and have dots
    if '.' in token:
        parts = token.split('.')
        print(f"\n✅ Looks like JWT format")
        print(f"   Parts: {len(parts)} (should be 3)")
        
        if len(parts) != 3:
            print(f"   ⚠️  Expected 3 parts (header.payload.signature)")
            return False
    else:
        print(f"\n⚠️  Doesn't look like JWT (no dots)")
        print(f"   Expected format: xxx.yyy.zzz")
        return False
    
    # Check if it starts with eyJ (base64 for {"...)
    if token.startswith('eyJ'):
        print(f"   ✅ Starts with 'eyJ' (valid JWT header)")
    else:
        print(f"   ⚠️  Doesn't start with 'eyJ'")
    
    return True

def compare_with_example():
    """Compare your token with the example from Lava docs"""
    
    print("\n" + "="*70)
    print("📚 COMPARING WITH LAVA EXAMPLE")
    print("="*70)
    
    print("\n🔍 The curl example in your screenshot shows:")
    print("   Authorization: Bearer eyJzZWNyZXRfa2V5Ijoi...")
    print()
    print("   This is the exact format your token should be in.")
    print()
    print("   Your .env should have:")
    print("   LAVA_FORWARD_TOKEN=eyJzZWNyZXRfa2V5Ijoi...")
    print("   (the entire long string)")

async def main():
    print("\n🧪 LAVA API DEBUGGING")
    print("="*70)
    print("This will test your Lava token and API access\n")
    
    # Check token format
    format_ok = await test_token_format()
    
    if not format_ok:
        print("\n❌ Token format issue detected")
        compare_with_example()
        return
    
    # Make actual API call
    success = await test_lava_direct()
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    if success:
        print("\n🎉 LAVA API IS WORKING!")
        print("\nYour token is valid and Lava is responding.")
        print("The issue must be in how the agent is using it.")
        print("\nNext steps:")
        print("  1. Check logs/response_agent.log for detailed errors")
        print("  2. Look for the exact error message from Lava")
        print("  3. The agent might need to be restarted")
        print("\nRestart agents:")
        print("  pkill -f 'python.*agent'")
        print("  ./setup_e2e_test.sh")
    else:
        print("\n❌ LAVA API TEST FAILED")
        print("\nSee errors above for details.")
        print("\nCommon fixes:")
        print("  • Token expired: Get new token from Lava dashboard")
        print("  • Insufficient funds: Add money to Lava wallet")
        print("  • Wrong token: Copy the 'Forward Token' from dashboard")
    
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())