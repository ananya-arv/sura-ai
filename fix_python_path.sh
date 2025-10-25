#!/bin/bash

echo "🔧 Fixing Python Import Issues"
echo "================================"

# Get the project root directory
PROJECT_ROOT=$(pwd)

echo ""
echo "📂 Project Root: $PROJECT_ROOT"

# Option 1: Create __init__.py files (makes it a proper package)
echo ""
echo "1️⃣  Creating __init__.py files..."

touch agents/__init__.py
touch agents/canary/__init__.py
touch agents/monitoring/__init__.py
touch agents/response/__init__.py
touch agents/communication/__init__.py
touch services/__init__.py

echo "   ✅ Created __init__.py files"

# Option 2: Set PYTHONPATH
echo ""
echo "2️⃣  Setting PYTHONPATH..."

# Add to current shell
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "   ✅ PYTHONPATH set to: $PYTHONPATH"

# Option 3: Create a startup script that sets PYTHONPATH
echo ""
echo "3️⃣  Creating run_agent.sh helper..."

cat > run_agent.sh << 'EOF'
#!/bin/bash
# Helper script to run agents with correct PYTHONPATH

export PYTHONPATH="$(pwd):${PYTHONPATH}"
python "$@"
EOF

chmod +x run_agent.sh

echo "   ✅ Created run_agent.sh"

# Test if it works
echo ""
echo "4️⃣  Testing import..."

python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from agents.base_agent import BaseSuraAgent
print('   ✅ Import successful!')
" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "================================"
    echo "✅ FIX SUCCESSFUL!"
    echo "================================"
    echo ""
    echo "Now you can run agents with:"
    echo "  export PYTHONPATH=\$(pwd)"
    echo "  python agents/canary/canary_agent.py"
    echo ""
    echo "Or use the helper:"
    echo "  ./run_agent.sh agents/canary/canary_agent.py"
    echo ""
    echo "Or run the full test:"
    echo "  ./setup_e2e_test.sh"
else
    echo ""
    echo "⚠️  Still having issues. Try running:"
    echo "  export PYTHONPATH=\$(pwd)"
    echo "  python diagnose_agents.py"
fi