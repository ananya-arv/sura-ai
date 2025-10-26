#!/usr/bin/env python3
"""
Fix send_to_peer to work with Agentverse Mailbox
The issue: agents use mailbox to receive but not to send
"""

from pathlib import Path
import shutil

def main():
    print("="*70)
    print("🔧 FIXING AGENTVERSE MAILBOX COMMUNICATION")
    print("="*70)
    
    base_agent_file = Path("agents/base_agent.py")
    
    if not base_agent_file.exists():
        print("❌ agents/base_agent.py not found!")
        return
    
    # Backup
    backup = Path("agents/base_agent.py.backup_agentverse")
    shutil.copy(base_agent_file, backup)
    print(f"✅ Backed up to {backup}")
    
    # Read current content
    with open(base_agent_file, 'r') as f:
        lines = f.readlines()
    
    # Find and replace the send_to_peer method
    new_lines = []
    in_send_to_peer = False
    skip_until_next_method = False
    indent_count = 0
    
    for i, line in enumerate(lines):
        # Detect start of send_to_peer method
        if 'async def send_to_peer(self, ctx: Context, peer_name: str, message: Model)' in line:
            in_send_to_peer = True
            indent_count = len(line) - len(line.lstrip())
            
            # Write the NEW send_to_peer method
            indent = ' ' * indent_count
            new_lines.append(line)  # Keep the method signature
            new_lines.append(f'{indent}    """\n')
            new_lines.append(f'{indent}    Send message to peer using Agentverse mailbox routing\n')
            new_lines.append(f'{indent}    Works with mailbox=True agents\n')
            new_lines.append(f'{indent}    """\n')
            new_lines.append(f'{indent}    address = self.get_peer_address(peer_name)\n')
            new_lines.append(f'{indent}    if not address:\n')
            new_lines.append(f'{indent}        logger.error(f"❌ Cannot send to {{peer_name}} - not in registry")\n')
            new_lines.append(f'{indent}        return False\n')
            new_lines.append(f'{indent}    \n')
            new_lines.append(f'{indent}    try:\n')
            new_lines.append(f'{indent}        # Use ctx.send - it handles Agentverse mailbox routing automatically\n')
            new_lines.append(f'{indent}        await ctx.send(address, message)\n')
            new_lines.append(f'{indent}        logger.info(f"✅ Sent {{message.__class__.__name__}} to {{peer_name}}")\n')
            new_lines.append(f'{indent}        return True\n')
            new_lines.append(f'{indent}    except Exception as e:\n')
            new_lines.append(f'{indent}        logger.error(f"❌ Failed to send to {{peer_name}}: {{e}}")\n')
            new_lines.append(f'{indent}        return False\n')
            
            skip_until_next_method = True
            continue
        
        # Skip old send_to_peer implementation
        if skip_until_next_method:
            # Check if we've reached the next method or end of class
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                # If we're back at class level or next method, stop skipping
                if current_indent <= indent_count and ('def ' in line or 'class ' in line):
                    skip_until_next_method = False
                    new_lines.append('\n')  # Add blank line
                    new_lines.append(line)
                    continue
            continue
        
        # Keep all other lines
        new_lines.append(line)
    
    # Write modified content
    with open(base_agent_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed send_to_peer to use Agentverse mailbox routing")
    
    print("\n" + "="*70)
    print("✅ AGENTVERSE COMMUNICATION FIXED!")
    print("="*70)
    print("\nWhat changed:")
    print("- send_to_peer now uses ctx.send() directly")
    print("- ctx.send() automatically routes through Agentverse mailbox")
    print("- No manual HTTP calls needed")
    print("\nNext steps:")
    print("\n1. Kill all agents:")
    print("   pkill -f 'python.*agent'")
    print("\n2. Restart them:")
    print("   ./setup_e2e_test.sh")
    print("\n3. Verify on Agentverse:")
    print("   https://agentverse.ai/agents")
    print("   All 4 agents should show 'Active'")
    print("\n4. Run test:")
    print("   python e2e_test_pipeline.py")
    print("\n✅ Agents will now communicate through Agentverse mailbox!")
    print("="*70)

if __name__ == "__main__":
    main()