# Creao Dashboard - Demo Guide

## 🎯 Overview

This dashboard has been redesigned specifically for demo presentations to judges, with focus on **showcasing agent network communication** during anomaly detection and remediation.

## ✨ Key Features

### 1. **Live Agent Network (HERO SECTION)**
- **Location:** Top of dashboard - largest, most prominent element
- **Visual Design:**
  - 4 large agent cards (Canary, Monitoring, Response, Communication)
  - Animated glow effects when agents are active
  - Animated arrows showing message flow between agents
  - Status indicators below each agent (Active/Idle)
- **Stage Indicator:** Shows current phase (DETECTION, ASSESSMENT, EXECUTION, RESOLUTION)
- **Message Preview:** Displays inter-agent communication messages below the network

### 2. **Timing - Optimized for Explanation**
- **Per Scenario:** 12-15 seconds
  - Detection: 3-5 seconds
  - Assessment: 5-7 seconds
  - Execution: 3-5 seconds
  - Resolution: 2-3 seconds
- **Between Scenarios:** 35 seconds (allows time to explain what happened)
- **Total Demo Time:** ~4 minutes for all 4 scenarios

### 3. **Button Text**
- Changed from "Run agent tests" → **"Activate System"**
- Gives feeling of activating a real monitoring system
- Disabled during operation, shows "System Active" with spinner

### 4. **System Status**
- **Minimized to compact badge** in top-right corner of header
- Shows: "🟢 Operational" or "🔴 Alert Active"
- Doesn't distract from main agent network

### 5. **Alert Card**
- Appears below agent network when anomaly detected
- Shows 4 states with color coding:
  - **Red:** DETECTED - Problem description
  - **Blue:** ASSESSING SOLUTION... (with spinner)
  - **Yellow:** Executing - Shows the action being taken
  - **Green:** Resolved - Shows final resolution
- Single alert at a time (replaces previous)
- Smooth fade-in animation (700ms)

### 6. **System Performance Metrics**
Judge-friendly metrics with explanations:

- **✅ Incidents Prevented:** {count}
  - → Bad updates caught before deploy

- **🎯 AI Decision Accuracy:** {95-99}%
  - → Success rate of AI-driven actions

- **⚡ Response Time:** {12-15}s
  - → Detection to resolution

- **🤖 Agent Collaboration:** {count} events
  - → Successful multi-agent workflows

Each metric has "View Details" button for deep dive explanations.

### 7. **Modal Popups**
Clean main dashboard with optional details:

#### **"View Live Logs"**
- Terminal-style log stream
- Color-coded by agent:
  - Cyan: Monitoring
  - Purple: Response
  - Yellow: Communication
  - Orange: Canary
- Searchable with filter input

#### **"View Scenarios"**
- List of all detected incidents
- Shows scenario icon, name, and timestamp
- Counter in button shows total observed

#### **"View Metrics Details"**
- Deep dive into each metric
- Explains "why this matters" for judges
- Full context on AI decision-making

## 🎬 Demo Flow Example

1. **Click "Activate System"**
2. **Agent Network activates** - All cards light up briefly
3. **First Alert Appears:**
   ```
   [Agent Network - TOP]
   🐦 Canary  →  👁️ Monitoring  →  🚑 Response  →  📢 Communication
   [Stage: DETECTION 🔍]
   Message: "Monitoring → Response: Canary deployment detected failures..."

   [Alert Card Below]
   ⚠️ DETECTED
   Canary deployment detected failures in version 2.3.1
   ```

4. **Assessment Phase (5-7 seconds):**
   ```
   [Stage changes to: ASSESSMENT 🤖]
   Message: "Response → Communication: Analyzing remediation options..."

   [Alert Card Updates]
   🤖 ASSESSING SOLUTION... (spinner)
   ```

5. **Execution Phase (3-5 seconds):**
   ```
   [Stage changes to: EXECUTION ⚡]
   Message: "Response → Communication: ROLLBACK to previous stable version..."

   [Alert Card Updates]
   ⚡ Executing: ROLLBACK to previous stable version 2.3.0
   ```

6. **Resolution (2-3 seconds):**
   ```
   [Stage changes to: RESOLUTION ✅]
   Message: "Communication: Incident resolved, system stable"

   [Alert Card Updates]
   ✅ Resolved: ROLLBACK to previous stable version 2.3.0
   ```

7. **35-second pause** - Explain what just happened to judges
8. **Next scenario begins...**

## 🚀 How to Run

### Start Backend:
```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Start the Flask API
python dashboard_live_api.py
```

The API runs on `http://localhost:3001`

### Frontend:
Already running in E2B environment, or:
```bash
npm run dev
```

### Activate Demo:
1. Open dashboard
2. Wait for "Connected" indicator (top-right)
3. Click **"Activate System"**
4. Watch the agent network visualization

## 📊 Scenarios

The system will demonstrate 4 incident types:

1. **🐦 Bad Software Update**
   - Problem: Canary deployment detected failures in version 2.3.1
   - Action: ROLLBACK to previous stable version 2.3.0

2. **📊 CPU Spike**
   - Problem: CPU usage at 95% on production-server-07
   - Action: SCALE horizontally - provision 3 additional instances

3. **🐛 Memory Leak**
   - Problem: Memory consumption increasing 2MB/min in payment-service
   - Action: RESTART affected service pods with heap dump capture

4. **⚡ Cascading Failure**
   - Problem: Database connection pool exhausted, 47 services degraded
   - Action: ACTIVATE circuit breakers and increase pool size to 200

## 🎨 Design Highlights

### Typography
- **Georgia serif** font throughout (matches SuraAI logo)
- Professional, readable, executive-friendly

### Color Scheme
- **Background:** Deep navy (#002147)
- **Text:** Off-white (#F7F7F0)
- **Alerts:** Red/Blue/Yellow/Green with 20% opacity backgrounds
- **Agent Glow:** White with shadow effects

### Animations
- **pulse-glow:** Active agents pulse with shadow
- **fade-in:** Smooth alert appearance
- **animate-pulse:** Status dots and arrows

## 💡 Tips for Judges Demo

1. **Start with agent network explanation:**
   - "These 4 agents work together to detect and resolve incidents"
   - "Watch how they communicate when an anomaly is detected"

2. **During first scenario:**
   - Point to Canary and Monitoring lighting up
   - "Canary detected a problem, now monitoring is assessing..."
   - Show the message flow

3. **After resolution:**
   - Use 35-second pause to explain:
     - What the agents decided
     - Why it was the right action
     - How it prevented an outage

4. **Reference metrics:**
   - "This is the {X}th incident we've prevented today"
   - "Our AI decision accuracy is {95-99}%"
   - Click "View Details" to dive deeper

5. **Optional deep dives:**
   - "View Live Logs" for technical audiences
   - "View Scenarios" to show what's been observed
   - Metrics details for ROI discussion

## 🔧 Configuration

### Adjust Timing
Edit `/home/user/vite-template/e2e_test_pipeline.py`:

```python
# Change cooldown between scenarios (line ~135)
time.sleep(35)  # Currently 35 seconds

# Change phase durations
time.sleep(3)  # Detection phase
time.sleep(3)  # Assessment phase
time.sleep(1)  # Execution steps
```

### Adjust Scenarios
Edit scenarios list in `e2e_test_pipeline.py` (lines 11-40)

## ✅ Validation

Run TypeScript/ESLint validation:
```bash
npm run check:safe
```

All checks pass ✓

## 🎯 Success Criteria

- [x] Agent Network is hero element at top
- [x] Clear visual communication flows
- [x] Stage indicators show current phase
- [x] 30-45 second gaps for explanation
- [x] System status minimized to badge
- [x] Scenarios moved to modal
- [x] Metrics are judge-friendly with explanations
- [x] Button text: "Activate System"
- [x] Clean single-screen layout
- [x] Georgia font throughout
- [x] All modals functional
- [x] TypeScript validation passes

## 📝 What Changed from Previous Version

### Major Changes:
1. **Agent Network moved to TOP** (was middle/bottom)
2. **Larger agent cards** (140x140px with glow effects)
3. **Stage indicator badge** shows current phase
4. **Message preview** shows inter-agent communication
5. **System status minimized** to small badge in header
6. **Scenarios moved to modal** (was main view)
7. **Metrics redesigned** with icons, large numbers, explanations
8. **Timing extended** to 35s between scenarios (was 15s)
9. **4-phase flow** added Resolution phase (was 3 phases)
10. **Button text** changed to "Activate System"

### Visual Improvements:
- Animated glow effects on active agents
- Pulsing arrows showing message flow
- Cleaner single-screen layout
- More prominent typography
- Color-coded alert states

The dashboard is now **demo-ready** with focus on showing judges exactly how the agent network communicates to detect and resolve incidents autonomously.
