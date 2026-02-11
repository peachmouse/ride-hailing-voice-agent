# 🚀 Start Here - Run Your Voice Agent

Your configuration is complete! Follow these steps to start your voice agent.

## ✅ Configuration Status

- ✅ LiveKit URL: `wss://voice-agent-101-6xk3trol.livekit.cloud`
- ✅ LiveKit API Key: Configured
- ✅ LiveKit API Secret: Configured
- ✅ OpenAI API Key: Configured
- ✅ Deepgram API Key: Configured

## 🎯 Quick Start (4 Steps)

You'll need **4 terminal windows** open. Here's the order:

### Terminal 1: Backend Setup & Install

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Install dependencies (first time only)
uv sync

# Download required models (first time only)
make download-files
```

**Wait for:** Models to download (this may take a few minutes the first time)

### Terminal 2: Start LangGraph Server

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start LangGraph server
make langgraph-dev
```

**Wait for:** `LangGraph server running on http://localhost:2024`

**Keep this terminal open!**

### Terminal 3: Start Backend Agent

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"

# Start the LiveKit agent
make dev
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

## 📊 What Should Be Running

You should have 4 processes running:
1. ✅ **LangGraph Server** (Terminal 2) - Port 2024
2. ✅ **Backend Agent** (Terminal 3) - Connected to LiveKit Cloud
3. ✅ **Frontend** (Terminal 4) - Port 3000
4. ✅ **Browser** - http://localhost:3000

## 🐛 Troubleshooting

### "Cannot connect to LiveKit"
- Check Terminal 3 (backend agent) for connection errors
- Verify your LiveKit credentials in `.env` files
- Check that LiveKit Cloud project is active

### "Agent not responding"
- Check Terminal 3 (backend agent) for errors
- Verify Terminal 2 (LangGraph server) is still running
- Check browser console (F12) for errors

### "Module not found" or import errors
- Make sure you ran `uv sync` in Terminal 1
- Try: `cd backend/langgraph-voice-call-agent && uv sync`

### Frontend won't start
- Make sure you ran `npm install` in Terminal 4
- Check Node.js version: `node --version` (should be 18+)

## 🎉 Success Indicators

When everything is working, you should see:
- ✅ LangGraph server logs showing it's ready
- ✅ Backend agent logs showing it's connected to LiveKit
- ✅ Frontend loads at http://localhost:3000
- ✅ You can click "Start Voice Call" and connect
- ✅ Agent responds to your voice

## 📝 Next Steps

Once it's working:
- Try asking the agent to manage todos: "Add a todo to buy groceries"
- Test voice interactions
- Customize the agent in `backend/langgraph-voice-call-agent/src/langgraph/agent.py`
- Modify the UI in `frontend/langgraph-voice-call-agent-web/components/`

---

**Need help?** Check the logs in each terminal for specific error messages.

