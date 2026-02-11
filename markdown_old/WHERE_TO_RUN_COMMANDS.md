# 📍 Where to Run Commands

## Directory Structure

```
langgraph-voice-back2front/
├── backend/
│   └── langgraph-voice-call-agent/    ← Run backend commands HERE
│       ├── src/
│       ├── .env
│       ├── pyproject.toml
│       └── ...
└── frontend/
    └── langgraph-voice-call-agent-web/  ← Run frontend commands HERE
        ├── app/
        ├── .env.local
        ├── package.json
        └── ...
```

## ✅ Correct Paths

### For Backend Commands (LangGraph & Agent)

**Full Path:**
```
C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent
```

**Quick Navigation:**
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
```

### For Frontend Commands

**Full Path:**
```
C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web
```

**Quick Navigation:**
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web"
```

## 🎯 Step-by-Step Commands

### Terminal 1: LangGraph Server

```powershell
# Navigate to backend directory
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start LangGraph server
uv run langgraph dev
```

**Wait for:** `LangGraph server running on http://localhost:2024`

### Terminal 2: Backend Agent

```powershell
# Navigate to backend directory (same as Terminal 1)
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start the agent
uv run -m src.livekit.agent dev
```

**Wait for:** `connecting to room...` or `worker started`

### Terminal 3: Frontend

```powershell
# Navigate to frontend directory
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web"

# Start frontend
npm run dev
```

**Wait for:** `Ready on http://localhost:3000`

## 📝 Quick Reference

| Command | Directory |
|---------|-----------|
| `uv run langgraph dev` | `backend\langgraph-voice-call-agent` |
| `uv run -m src.livekit.agent dev` | `backend\langgraph-voice-call-agent` |
| `npm run dev` | `frontend\langgraph-voice-call-agent-web` |

## ✅ Verification

To verify you're in the right directory, check for these files:

**Backend directory should have:**
- `pyproject.toml`
- `src/` folder
- `.env` file

**Frontend directory should have:**
- `package.json`
- `app/` folder
- `.env.local` file

## 🚀 Quick Start (Copy-Paste Ready)

**Terminal 1:**
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run langgraph dev
```

**Terminal 2:**
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run -m src.livekit.agent dev
```

**Terminal 3:**
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web"
npm run dev
```

Then open: **http://localhost:3000**

