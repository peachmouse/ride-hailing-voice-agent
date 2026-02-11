# Quick Start Guide

Get your LangGraph Voice Agent running in 5 minutes!

## ⚠️ Using LiveKit Cloud?

If you have LiveKit Cloud credentials (API key starting with "API"), **skip Step 2** (Docker setup) and see [CONFIGURATION.md](./CONFIGURATION.md) for cloud setup instructions.

## Prerequisites Check

Before starting, make sure you have:
- ✅ Docker Desktop installed and running (only if using local LiveKit server)
- ✅ Python 3.12+ with `uv` installed
- ✅ Node.js 18+ installed
- ✅ API keys: OpenAI, Deepgram, and LiveKit (if using cloud)

## Step 1: Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd backend/langgraph-voice-call-agent

# Install dependencies
uv sync

# Download required models
make download-files

# Create .env file (copy from .env.example and add your API keys)
# Edit .env with your OPENAI_API_KEY and DEEPGRAM_API_KEY
```

## Step 2: Start LiveKit Server (Terminal 1)

**Skip this step if using LiveKit Cloud** - see [CONFIGURATION.md](./CONFIGURATION.md)

```bash
# Still in backend/langgraph-voice-call-agent
docker compose up -d

# Verify it's running
docker compose ps
```

## Step 3: Start LangGraph Server (Terminal 2)

```bash
cd backend/langgraph-voice-call-agent
make langgraph-dev
```

Wait for: `LangGraph server running on http://localhost:2024`

## Step 4: Start Backend Agent (Terminal 3)

```bash
cd backend/langgraph-voice-call-agent
make dev
```

Wait for: `connecting to room...` (agent is ready)

## Step 5: Frontend Setup (Terminal 4)

```bash
# Navigate to frontend
cd frontend/langgraph-voice-call-agent-web

# Install dependencies
npm install
# or
pnpm install

# Create .env.local file (copy from .env.local.example)
# For local: LIVEKIT_URL=ws://localhost:7880, LIVEKIT_API_KEY=devkey, LIVEKIT_API_SECRET=secret
# For cloud: See CONFIGURATION.md for your LiveKit Cloud credentials

# Start frontend
npm run dev
# or
pnpm dev
```

## Step 6: Test It!

1. Open your browser to `http://localhost:3000`
2. Click **"Start Voice Call"**
3. Allow microphone access when prompted
4. Start talking! The agent should respond

## Troubleshooting

### "Connection failed" in browser
- Check LiveKit server: `docker compose ps` (should show running)
- Verify `.env.local` has correct credentials
- Check browser console for specific errors

### "Agent not responding"
- Check backend agent terminal for connection logs
- Verify LangGraph server is running on port 2024
- Check that all API keys are set in backend `.env`

### "Cannot connect to LiveKit"
- Ensure Docker is running
- Check ports 7880, 7881, 7882 are not in use
- Restart LiveKit: `docker compose restart`

## What's Running?

You should have 4 terminals/processes:
1. **LiveKit Server** (Docker) - Port 7880
2. **LangGraph Server** - Port 2024
3. **Backend Agent** - Connected to LiveKit
4. **Frontend** - Port 3000

## Next Steps

- Customize the agent in `backend/langgraph-voice-call-agent/src/langgraph/agent.py`
- Modify UI in `frontend/langgraph-voice-call-agent-web/components/`
- See `SETUP.md` for detailed configuration options

