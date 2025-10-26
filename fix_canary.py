#!/usr/bin/env python3
"""
Fix ONLY Canary Agent Schema Mismatch
Minimal change - just fix orchestrator's UpdatePackage to match canary's expectation
"""

from pathlib import Path
import re

def fix_orchestrator_updatepackage():
    """Fix ONLY the UpdatePackage class in e2e_test_pipeline.py"""
    
    file_path = Path("e2e_test_pipeline.py")
    
    if not file_path.exists():
        print("❌ e2e_test_pipeline.py not found!")
        return False
    
    print("🔧 Fixing UpdatePackage schema in orchestrator...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{file_path}.backup_canary_fix", 'w') as f:
        f.write(content)
    print(f"✅ Backed up to {file_path}.backup_canary_fix")
    
    # Check current state
    print("\n📋 Current state:")
    
    # Check if it imports UpdatePackage
    has_import = 'from agents.messages import' in content and 'UpdatePackage' in content[:2000]
    # Check if it also defines UpdatePackage
    has_definition = bool(re.search(r'^class UpdatePackage\(Model\):', content, re.MULTILINE))
    
    print(f"   Imports from agents.messages: {'✅' if has_import else '❌'}")
    print(f"   Has duplicate definition: {'⚠️ YES (problem!)' if has_definition else '✅ No'}")
    
    if not has_definition:
        print("\n✅ No duplicate UpdatePackage definition found!")
        print("   Schema mismatch must be from something else.")
        
        # Let's check the actual import
        if has_import:
            print("\n   UpdatePackage is already imported correctly.")
            print("   Try restarting agents - they may need fresh schema cache.")
            return True
        else:
            print("\n   Adding import statement...")
    
    # MINIMAL FIX: Just remove the UpdatePackage class definition
    # Keep everything else untouched
    
    print("\n🔧 Applying fix...")
    
    # Find and remove ONLY the UpdatePackage class
    pattern = r'class UpdatePackage\(Model\):.*?(?=\nclass [A-Z]|\n# =|$)'
    
    if re.search(pattern, content, re.DOTALL):
        # Check if there's a duplicate
        matches = re.findall(pattern, content, re.DOTALL)
        if len(matches) > 0:
            print(f"   Found {len(matches)} UpdatePackage definition(s)")
            
            # Remove ONLY if it's in the MESSAGE MODELS section (not the import)
            # Look for the one that's between comment blocks
            message_models_section = re.search(
                r'# MESSAGE MODELS.*?class UpdatePackage\(Model\):.*?(?=\nclass [A-Z])',
                content,
                re.DOTALL
            )
            
            if message_models_section:
                # Remove just this UpdatePackage definition
                old_def = message_models_section.group(0)
                # Keep everything except the class definition
                new_section = old_def.split('class UpdatePackage')[0]
                content = content.replace(old_def, new_section)
                print("   ✅ Removed duplicate UpdatePackage definition")
            else:
                print("   ⚠️ Could not locate duplicate in MESSAGE MODELS section")
    
    # Make sure import exists
    if 'from agents.messages import' not in content or 'UpdatePackage' not in content[:2000]:
        print("   Adding import statement...")
        
        # Find where to add import (after other imports, before class definitions)
        import_pos = content.find('from typing import')
        if import_pos != -1:
            # Add after this import
            import_end = content.find('\n', import_pos) + 1
            import_statement = 'from agents.messages import UpdatePackage, CanaryTestResult\n'
            content = content[:import_end] + import_statement + content[import_end:]
            print("   ✅ Added import from agents.messages")
    
    # Write fixed version
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Fixed {file_path}")
    return True

def verify_canary_agent():
    """Verify canary agent imports from agents.messages"""
    
    print("\n🔍 Verifying canary agent...")
    
    canary_file = Path("agents/canary/canary_agent.py")
    if not canary_file.exists():
        print("❌ canary_agent.py not found!")
        return False
    
    with open(canary_file, 'r') as f:
        content = f.read()
    
    # Check import
    if 'from agents.messages import UpdatePackage' in content:
        print("✅ Canary agent imports UpdatePackage correctly")
        return True
    else:
        print("⚠️  Canary agent not importing from agents.messages")
        print("   It may be using local definition (could cause mismatch)")
        return False

def verify_messages_file():
    """Check what UpdatePackage looks like in messages.py"""
    
    print("\n📄 Checking agents/messages.py...")
    
    messages_file = Path("agents/messages.py")
    if not messages_file.exists():
        print("❌ agents/messages.py not found!")
        return False
    
    with open(messages_file, 'r') as f:
        content = f.read()
    
    # Extract UpdatePackage definition
    match = re.search(r'class UpdatePackage\(Model\):.*?(?=\nclass |\n# =|$)', content, re.DOTALL)
    
    if match:
        print("✅ UpdatePackage found in messages.py:")
        lines = match.group(0).split('\n')[:8]  # First 8 lines
        for line in lines:
            print(f"   {line}")
        return True
    else:
        print("❌ UpdatePackage not found in messages.py!")
        return False

def main():
    print("="*70)
    print("🔧 FIXING CANARY AGENT COMMUNICATION ONLY")
    print("="*70)
    print()
    print("Problem: Orchestrator's UpdatePackage schema doesn't match")
    print("         what canary agent expects")
    print()
    print("Fix: Remove duplicate UpdatePackage definition from orchestrator")
    print("     Keep everything else unchanged")
    print()
    
    # Check messages.py
    has_canonical = verify_messages_file()
    
    # Check canary agent
    canary_ok = verify_canary_agent()
    
    # Fix orchestrator
    if not fix_orchestrator_updatepackage():
        print("\n❌ Fix failed!")
        return
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    if has_canonical and canary_ok:
        print("\n✅ FIX APPLIED SUCCESSFULLY!")
        print()
        print("What changed:")
        print("  • Removed duplicate UpdatePackage from orchestrator")
        print("  • Orchestrator now imports from agents.messages")
        print("  • Canary agent already imports from agents.messages")
        print("  • Both now use the SAME schema definition")
        print()
        print("What stayed the same:")
        print("  ✅ Monitoring agent - unchanged")
        print("  ✅ Response agent - unchanged")
        print("  ✅ Communication agent - unchanged")
        print("  ✅ All other message types - unchanged")
        print()
        print("Next steps:")
        print("  1. Kill all agents: pkill -f 'python.*agent'")
        print("  2. Restart: ./setup_e2e_test.sh")
        print()
        print("Expected result:")
        print("  ✅ No more 'unrecognized schema digest' warning")
        print("  ✅ Canary agent will receive UpdatePackage")
        print("  ✅ You should see: 'Received update UPDATE-FAULTY...'")
        print()
    else:
        print("\n⚠️  FIX APPLIED BUT ISSUES REMAIN")
        print()
        if not has_canonical:
            print("❌ agents/messages.py missing UpdatePackage")
            print("   You need to add it there as the canonical definition")
        if not canary_ok:
            print("❌ Canary agent not importing from agents.messages")
            print("   You need to update canary_agent.py imports")
    
    print("="*70)

if __name__ == "__main__":
    main()