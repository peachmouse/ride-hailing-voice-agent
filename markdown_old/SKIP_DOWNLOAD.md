# ✅ Solution: Skip Model Download

## The Problem

The `download-files` command is timing out when trying to download models from HuggingFace. This is a common network issue.

## The Solution

**You can safely skip the `download-files` step!** The models will download automatically when you start the agent.

## What to Do Instead

Just start the services directly:

### 1. Start LangGraph Server (Terminal 1)
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run langgraph dev
```

### 2. Start Backend Agent (Terminal 2)
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run -m src.livekit.agent dev
```

The agent will automatically download any missing models when it starts. This may take a few minutes the first time, but it will work.

### 3. Start Frontend (Terminal 3)
```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\frontend\langgraph-voice-call-agent-web"
npm install  # first time only
npm run dev
```

## Why This Works

The LiveKit agent framework downloads models on-demand when they're first needed. The `download-files` command is just a convenience to pre-download them, but it's not required.

## If You Still Want to Pre-download

If you really want to pre-download the models (optional), you can try:

1. **Increase timeout** (if the library supports it)
2. **Use a VPN** if HuggingFace is blocked/slow in your region
3. **Retry later** when network conditions are better
4. **Just wait** - the agent will download them automatically anyway

But honestly, **just skip it and start the agent** - it's the easiest solution!

