# SuraAI Disaster Recovery Dashboard

A professional, production-ready monitoring dashboard that demonstrates real-time disaster recovery scenarios with autonomous agent responses.

## 🎯 Features

### Single-Screen Design
- **No scrolling required** - Everything visible on one viewport
- **Single alert card** - Shows one alert at a time with smooth transitions
- **Scenarios Observed** - Dynamic list that grows as new incident types are detected
- **Clean, minimal** - Professional monitoring dashboard aesthetic

### Realistic Timing
- **10-15 seconds between alerts** - Feels like real production monitoring
- **Phased execution**:
  - Detecting (10-12s)
  - Assessing (8-10s)
  - Executing (7-10s)
- **15-second cooldown** between scenarios

### Live Logs Modal
- **Separate view** - Keeps main dashboard clean
- **Real-time streaming** - Terminal-style log display
- **Color-coded agents**:
  - 🔵 Monitoring (cyan)
  - 🟣 Response (purple)
  - 🟡 Communication (yellow)
  - 🟠 Canary (orange)
- **Searchable** - Filter logs in real-time

### Typography
- **Georgia serif** font throughout (matches SuraAI logo)
- **Consistent branding** - Professional appearance

## 🚀 Quick Start

### Prerequisites
```bash
# Python dependencies
pip install flask flask-cors

# Node.js dependencies (already installed)
npm install
```

### Running the Dashboard

1. **Start the backend API** (in one terminal):
```bash
python dashboard_live_api.py
```

Expected output:
```
🚀 SuraAI Dashboard API starting on http://localhost:3001
Frontend should connect to this server

Endpoints:
  GET  /api/status - Get system state
  GET  /api/logs   - Get recent logs
  POST /api/run-tests - Start test pipeline
```

2. **Open the frontend** (in your browser):
   - If using E2B, the preview URL is already provided
   - If running locally: `npm run dev` (then open http://localhost:5173)

3. **Click "Run agent tests"** in the dashboard

4. **Watch the monitoring** happen in real-time:
   - System Status changes color based on phase
   - Alert card appears with detection
   - Scenarios Observed list grows
   - Agents activate/deactivate
   - Metrics update

5. **Click "View Live Logs"** to see detailed system logs

## 📊 Dashboard Sections

### System Status (Top)
Dynamic status bar showing:
- **Operational** (blue-green) - Normal monitoring
- **Alert** (red-orange) - Anomaly detected
- **Assessing** (blue-purple) - Analyzing solution
- **Executing** (green-teal) - Implementing fix

### Alert Card
Single card showing:
- **DETECTED** header
- **Problem description**
- **Processing status** ("ASSESSING SOLUTION...")
- **Final action** taken (green box)

### Scenarios Observed
Simple list that accumulates:
- Scenario name + icon
- Timestamp when first detected
- No duplicates

### Metrics
- Tests run
- Bad updates caught
- Anomalies detected
- Autonomous recoveries
- Incidents prevented

### Active Agents
Visual pipeline showing 4 agents:
- Canary
- Monitor
- Response
- Communicator

### Scenario Progress
Real-time checklist of scenarios:
- Bad Software Update 🐦
- CPU Spike 📊
- Memory Leak 🐛
- Cascading Failure ⚡

## 🔧 Technical Details

### Architecture
```
Frontend (React + TypeScript)
    ↕ HTTP polling (1s interval)
Backend API (Flask)
    ↕ Function calls
Test Pipeline (Python)
```

### API Endpoints

**GET /api/status**
Returns current system state:
```json
{
  "running": true,
  "current_scenario": {...},
  "phase": "detecting",
  "active_agents": ["canary", "monitoring"],
  "metrics": {...},
  "completed_scenarios": [1, 2]
}
```

**GET /api/logs**
Returns recent logs (last 50):
```json
[
  {
    "timestamp": "2025-01-15T10:30:45.123Z",
    "type": "info",
    "message": "Agent 'monitoring' activated",
    "agent": "monitoring"
  }
]
```

**POST /api/run-tests**
Starts the test pipeline

### Timing Breakdown

Each scenario takes ~40-45 seconds:
- Detecting: 10-12s
- Assessing: 8-10s
- Executing: 7-10s
- Cooldown: 15s

Full pipeline (4 scenarios): ~3 minutes

## 🎨 Design Principles

1. **Single-screen** - No scrolling, all critical info visible
2. **Progressive disclosure** - Logs hidden in modal
3. **Realistic pacing** - Feels like production monitoring
4. **Clear hierarchy** - Status → Alert → Details
5. **Consistent typography** - Georgia serif everywhere

## 🐛 Troubleshooting

### "Backend not running" error
- Make sure `python dashboard_live_api.py` is running
- Check that port 3001 is available
- Verify Flask and flask-cors are installed

### No alerts appearing
- Wait 15-20 seconds after clicking "Run agent tests"
- Check browser console for errors
- Verify API connection indicator shows "Connected"

### Logs not updating
- Click "View Live Logs" button (top right)
- Check that API is running and returning data
- Clear browser cache and refresh

## 📝 Customization

### Adjust timing
Edit `e2e_test_pipeline.py`:
```python
# Line 135: Cooldown between scenarios
time.sleep(15)  # Change to desired seconds

# Lines 63, 82, 111: Phase durations
time.sleep(8)  # Detection time
time.sleep(6)  # Assessment time
time.sleep(1.5)  # Execution step time
```

### Add new scenarios
Edit `e2e_test_pipeline.py`:
```python
SCENARIOS = [
    {
        "id": 5,
        "name": "Your Scenario",
        "icon": "🔥",
        "problem": "Description of the problem",
        "action": "Action to resolve it"
    }
]
```

### Change colors
Edit `src/routes/index.tsx` - look for gradient classes:
```tsx
"bg-gradient-to-r from-blue-900/30 to-green-900/30"
```

## 📄 License

MIT License - feel free to use for demos, presentations, or production monitoring

## 🙏 Credits

Built with:
- React 19 + TypeScript
- TailwindCSS v4
- shadcn/ui components
- Flask (Python backend)
- Georgia serif typography
