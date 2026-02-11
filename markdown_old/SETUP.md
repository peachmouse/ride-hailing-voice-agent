# Setup Guide: Connecting Frontend and Backend

This guide will help you connect the frontend and backend of the LangGraph Voice Agent so you can run the agent in your browser.

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │ LiveKit     │ <────── │   Backend   │
│  (Next.js)  │ WebSocket│   Server    │ WebSocket│  (Python)   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              │
                        ┌─────────────┐
                        │  LangGraph  │
                        │   Server    │
                        └─────────────┘
```

1. **Frontend (Next.js)**: Web UI that connects to LiveKit server
2. **LiveKit Server**: Real-time communication server (local via Docker or cloud)
3. **Backend (Python)**: LiveKit agent that processes voice and connects to LangGraph
4. **LangGraph Server**: Runs your agent graph

## Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Python** 3.12+ with `uv` package manager
- **Docker & Docker Compose** (for local LiveKit server)
- **API Keys**:
  - OpenAI API key (for LangGraph agent)
  - Deepgram API key (for STT/TTS)

## Step-by-Step Setup

### 1. Backend Setup

#### 1.1 Install Dependencies

```bash
cd backend/langgraph-voice-call-agent
uv sync
```

#### 1.2 Download Required Model Files

```bash
make download-files
# or
uv run -m src.livekit.agent download-files
```

#### 1.3 Configure Environment Variables

Create a `.env` file in `backend/langgraph-voice-call-agent/`:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=your-openai-api-key
DEEPGRAM_API_KEY=your-deepgram-api-key
LANGGRAPH_URL=http://localhost:2024
```

### 2. Start LiveKit Server (Local Development)

The backend includes a Docker Compose setup for local development:

```bash
cd backend/langgraph-voice-call-agent
docker compose up -d
```

This starts a LiveKit server on:
- Port 7880: HTTP/WebSocket API
- Port 7881: TURN/TLS
- Port 7882: UDP for media

**Verify it's running:**
```bash
docker compose ps
docker compose logs livekit
```

### 3. Start LangGraph Server

The backend agent needs a LangGraph server running. In a new terminal:

```bash
cd backend/langgraph-voice-call-agent
make langgraph-dev
# or
uv run langgraph dev
```

This starts the LangGraph server on `http://localhost:2024` (default).

### 4. Start Backend Agent

In another terminal:

```bash
cd backend/langgraph-voice-call-agent
make dev
# or
uv run -m src.livekit.agent dev
```

**Or start both LangGraph and agent together:**
```bash
make dev-all
```

The agent will:
- Connect to the LiveKit server
- Wait for participants to join rooms
- Process voice interactions through LangGraph

### 5. Frontend Setup

#### 5.1 Install Dependencies

```bash
cd frontend/langgraph-voice-call-agent-web
npm install
# or if using pnpm (as specified in package.json)
pnpm install
```

#### 5.2 Configure Environment Variables

Create a `.env.local` file in `frontend/langgraph-voice-call-agent-web/`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your LiveKit credentials (same as backend):

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

**Important**: The frontend and backend must use the same LiveKit server credentials.

#### 5.3 Start Frontend Development Server

```bash
cd frontend/langgraph-voice-call-agent-web
npm run dev
# or
pnpm dev
```

The frontend will be available at `http://localhost:3000`.

## Testing the Connection

1. **Open the frontend**: Navigate to `http://localhost:3000`
2. **Click "Start Voice Call"**: This will:
   - Request connection details from `/api/connection-details`
   - Generate a LiveKit access token
   - Connect to the LiveKit server
   - Join a room
3. **Backend agent should connect**: When you join a room, the backend agent will:
   - Detect your participation
   - Initialize the voice assistant
   - Start processing audio

## How It Works

### Connection Flow

1. **Frontend** calls `/api/connection-details` (Next.js API route)
2. **API route** generates a LiveKit access token using `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`
3. **Frontend** connects to `LIVEKIT_URL` (LiveKit server) with the token
4. **Backend agent** (already connected to LiveKit server) detects the new participant
5. **Backend agent** initializes a session and starts processing voice/text
6. **LangGraph server** processes the conversation through the agent graph

### Key Components

- **`/api/connection-details/route.ts`**: Generates LiveKit tokens for frontend
- **`useConnectionDetails.ts`**: Frontend hook that fetches connection details
- **`app.tsx`**: Main frontend component that manages LiveKit room connection
- **`src/livekit/agent.py`**: Backend agent entrypoint
- **`src/livekit/adapter/langgraph.py`**: Bridges LiveKit to LangGraph

## Troubleshooting

### Frontend can't connect to LiveKit

**Symptoms**: Connection errors in browser console

**Solutions**:
1. Verify LiveKit server is running: `docker compose ps`
2. Check `.env.local` has correct `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
3. Ensure backend and frontend use the same LiveKit credentials
4. Check browser console for specific error messages

### Backend agent not connecting

**Symptoms**: No agent in room, no voice response

**Solutions**:
1. Verify agent is running: Check terminal for connection logs
2. Check backend `.env` has correct LiveKit credentials
3. Ensure LangGraph server is running on port 2024
4. Check agent logs for errors

### LangGraph connection errors

**Symptoms**: Agent can't reach LangGraph server

**Solutions**:
1. Verify LangGraph server is running: `uv run langgraph dev`
2. Check `LANGGRAPH_URL` in backend `.env` matches server URL
3. Default is `http://localhost:2024`

### Port conflicts

**Symptoms**: Can't start LiveKit server or services

**Solutions**:
```bash
# Stop existing containers
docker compose down

# Check what's using the ports
# Windows: netstat -ano | findstr :7880
# Linux/Mac: lsof -i :7880

# Restart services
docker compose up -d
```

## Production Deployment

For production, use **LiveKit Cloud** instead of local Docker:

1. Sign up at [LiveKit Cloud](https://cloud.livekit.io/)
2. Create a project and get API keys
3. Update both `.env` files with cloud credentials:
   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   ```
4. Deploy backend agent to a server/cloud platform
5. Deploy frontend to Vercel/Netlify/etc.

## Next Steps

- Customize the agent in `backend/langgraph-voice-call-agent/src/langgraph/agent.py`
- Modify UI in `frontend/langgraph-voice-call-agent-web/components/`
- Adjust configuration in `frontend/langgraph-voice-call-agent-web/app-config.ts`

## Additional Resources

- [LiveKit Agents Documentation](https://github.com/livekit/agents)
- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)
- [LiveKit Self-Hosting Guide](https://docs.livekit.io/home/self-hosting/)

