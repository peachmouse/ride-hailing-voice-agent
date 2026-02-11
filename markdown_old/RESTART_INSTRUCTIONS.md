# 🔄 Restart Instructions

## Quick Answer: YES, Restart the Agent

Since we changed the code (switched TTS from Hume to Deepgram), you should restart the agent to ensure the changes take effect.

## What to Restart

### ✅ Restart This:
- **Terminal 2: Backend Agent** - Restart to load the new TTS code

### ❌ Don't Restart These:
- **Terminal 1: LangGraph Server** - Keep running
- **Terminal 3: Frontend** - Keep running

## Step-by-Step Restart

### 1. Stop the Agent (Terminal 2)

In the terminal where the agent is running:
- Press `Ctrl+C` to stop the agent
- Wait for it to fully stop

### 2. Start the Agent Again (Terminal 2)

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run -m src.livekit.agent dev
```

### 3. Verify It Started

You should see:
- ✅ "starting worker"
- ✅ "registered worker"
- ✅ "Watching..." (file watching enabled)
- ✅ No errors about Hume API key

### 4. Test the Connection

1. Go to http://localhost:3000 in your browser
2. Click "Start Voice Call"
3. The agent should now connect successfully with Deepgram TTS

## Why Restart?

Even though the agent runs in dev mode with file watching, restarting ensures:
- The new code is definitely loaded
- All imports are refreshed
- The Deepgram TTS is properly initialized

## Quick Restart Command

If you're already in the backend directory:

```powershell
# Just press Ctrl+C, then:
uv run -m src.livekit.agent dev
```

That's it! The agent should now work with Deepgram TTS.

