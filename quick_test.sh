#!/bin/bash

echo "🧪 Running SuraAI Quick Test"
echo "============================"

# Test mock infrastructure
echo ""
echo "1️⃣ Testing Mock Infrastructure..."
curl -s http://localhost:8000/health | python -m json.tool

# Test deployment
echo ""
echo "2️⃣ Testing Update Deployment..."
curl -s -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": "TEST-QUICK-001",
    "version": "1.1.0",
    "target_systems": ["server-1", "server-2", "server-3"]
  }' | python -m json.tool

# Test failure simulation
echo ""
echo "3️⃣ Simulating Failure..."
curl -s -X POST http://localhost:8000/simulate-failure/server-1 | python -m json.tool

# Test rollback
echo ""
echo "4️⃣ Testing Rollback..."
curl -s -X POST http://localhost:8000/rollback/server-1 | python -m json.tool

echo ""
echo "✅ Quick test complete!"
