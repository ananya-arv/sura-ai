"""
Debug Lava Setup - Find out EXACTLY what's wrong
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("\n🔍 LAVA SETUP DEBUGGER")
    print("="*60)
    
    # Step 1: Check .env file exists
    print("\n1️⃣  Checking .env file...")
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env file exists at: {env_file.absolute()}")
    else:
        print(f"❌ .env file NOT FOUND!")
        print(f"   Expected location: {env_file.absolute()}")
        print(f"\n   Create it with:")
        print(f"   echo 'LAVA_FORWARD_TOKEN=your_token' > .env")
        return
    
    # Step 2: Load environment
    print("\n2️⃣  Loading .env file...")
    load_dotenv()
    print("✅ Environment loaded")
    
    # Step 3: Check LAVA_FORWARD_TOKEN
    print("\n3️⃣  Checking LAVA_FORWARD_TOKEN...")
    token = os.getenv("LAVA_FORWARD_TOKEN")
    
    if token is None:
        print("❌ LAVA_FORWARD_TOKEN is None (not set in environment)")
        print("\n   Checking .env file contents:")
        with open(".env", "r") as f:
            lines = f.readlines()
            found_lava = False
            for line in lines:
                if "LAVA" in line:
                    found_lava = True
                    print(f"   Found: {line.strip()}")
            if not found_lava:
                print("   ❌ No LAVA_FORWARD_TOKEN line found in .env!")
                print("\n   Add this line to .env:")
                print("   LAVA_FORWARD_TOKEN=lsk_live_your_token_here")
        return
    
    elif token == "":
        print("❌ LAVA_FORWARD_TOKEN is empty string")
        print("   Check .env file - make sure there's a value after =")
        return
    
    elif token.strip() != token:
        print("⚠️  LAVA_FORWARD_TOKEN has whitespace!")
        print(f"   Token: '{token}'")
        print("   Remove spaces/newlines from .env")
        return
    
    else:
        print(f"✅ LAVA_FORWARD_TOKEN found")
        print(f"   Length: {len(token)} characters")
        print(f"   Starts with: {token[:10]}...")
        print(f"   Ends with: ...{token[-5:]}")
        
        # Check if it looks valid
        if token.startswith("lsk_"):
            print("   ✅ Looks like valid Lava token (starts with lsk_)")
        else:
            print("   ⚠️  Token doesn't start with 'lsk_' (might be wrong)")
    
    # Step 4: Test lava_service import
    print("\n4️⃣  Testing lava_service import...")
    try:
        from services.lava_service import lava_service
        print("✅ lava_service imported successfully")
        
        print(f"\n   Service configuration:")
        print(f"   - Available: {lava_service.available}")
        print(f"   - Has token: {bool(lava_service.lava_token)}")
        print(f"   - Model: {lava_service.model}")
        print(f"   - URL: {lava_service.lava_url}")
        
        if lava_service.available:
            print("\n   ✅ LAVA IS ENABLED!")
        else:
            print("\n   ❌ LAVA IS DISABLED")
            print(f"   Token value in service: {lava_service.lava_token}")
            
    except Exception as e:
        print(f"❌ Failed to import lava_service: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Check other required tokens
    print("\n5️⃣  Checking other environment variables...")
    other_vars = [
        "CANARY_SEED_PHRASE",
        "MONITORING_SEED_PHRASE",
        "RESPONSE_SEED_PHRASE",
        "COMMUNICATION_SEED_PHRASE"
    ]
    
    for var in other_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...")
        else:
            print(f"⚠️  {var}: Not set (will use default)")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if lava_service.available:
        print("\n✅ LAVA IS WORKING!")
        print("\n   You can now run:")
        print("   python test_lava.py")
        print("\n   Or start your agents with Lava enabled")
    else:
        print("\n❌ LAVA IS NOT WORKING")
        print("\n   Most likely issue:")
        print("   - LAVA_FORWARD_TOKEN not in .env")
        print("   - Or .env file not being loaded")
        print("\n   Fix:")
        print("   1. Check .env exists in project root")
        print("   2. Add: LAVA_FORWARD_TOKEN=lsk_...")
        print("   3. Make sure no spaces around the =")
        print("   4. Save file and run this script again")
    
    print("="*60)

if __name__ == "__main__":
    main()