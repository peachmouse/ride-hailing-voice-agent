# 🪟 Windows Quick Start Guide

Since `make` isn't available on Windows, use these commands directly.

## ✅ Configuration Status

Your configuration is complete! All API keys are set up.

## 🎯 Quick Start (4 Steps)

You'll need **4 PowerShell terminal windows** open.

### Terminal 1: Backend Setup (One-time setup)

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Install dependencies (first time only)
uv sync

# ⚠️ SKIP download-files - it may timeout. Models will auto-download when agent starts!
# The download-files command often times out due to network issues with HuggingFace.
# This is fine - the models will download automatically when you start the agent.
```

### Terminal 2: Start LangGraph Server

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start LangGraph server
uv run langgraph dev
```

**Wait for:** `LangGraph server running on http://localhost:2024`

**Keep this terminal open!**

### Terminal 3: Start Backend Agent

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start the LiveKit agent
uv run -m src.livekit.agent dev
```

**Wait for:** `connecting to room...` or similar connection messages

**Keep this terminal open!**

### Terminal 4: Start Frontend

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web"

# Install dependencies (first time only)
npm install

# Start the frontend
npm run dev
```

**Wait for:** `Ready on http://localhost:3000`

## 🎤 Test It!

1. Open your browser to **http://localhost:3000**
2. Click **"Start Voice Call"**
3. Allow microphone access when prompted
4. Start talking! The agent should respond

## 📋 Command Reference (Windows)

Instead of `make <command>`, use:

| Make Command | Windows Command |
|-------------|----------------|
| `make download-files` | `uv run -m src.livekit.agent download-files` |
| `make dev` | `uv run -m src.livekit.agent dev` |
| `make langgraph-dev` | `uv run langgraph dev` |

## 🐛 Troubleshooting

### "Cannot instantiate this tokenizer" error
- This is a known issue with the turn detector model
- **Solution:** The models will download automatically when you start the agent
- You can skip the `download-files` step for now

### "Module not found" errors
- Make sure you ran `uv sync` in Terminal 1
- Try: `cd backend\langgraph-voice-call-agent && uv sync`

### "Cannot connect to LiveKit"
- Check Terminal 3 (backend agent) for connection errors
- Verify your LiveKit credentials in `.env` files

### Frontend won't start
- Make sure you ran `npm install` in Terminal 4
- Check Node.js version: `node --version` (should be 18+)

## 🎉 Success Indicators

When everything is working:
- ✅ LangGraph server logs showing it's ready (Terminal 2)
- ✅ Backend agent logs showing it's connected to LiveKit (Terminal 3)
- ✅ Frontend loads at http://localhost:3000 (Terminal 4)
- ✅ You can click "Start Voice Call" and connect
- ✅ Agent responds to your voice

---

**Note:** The `download-files` command may fail due to missing dependencies, but the models will download automatically when you start the agent, so you can skip that step.


