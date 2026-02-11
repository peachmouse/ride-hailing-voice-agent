# Configuration Guide

## Your LiveKit Credentials

You've provided your LiveKit API Key: `APIgCD5jBT47ogU`

**⚠️ Important:** You'll also need your **LiveKit API Secret** to complete the setup. This is typically shown alongside your API key in the LiveKit Cloud dashboard.

## Setup Steps

### 1. Get Your LiveKit API Secret

1. Go to your [LiveKit Cloud Dashboard](https://cloud.livekit.io/)
2. Navigate to your project settings
3. Find your API Secret (it will be different from your API Key)
4. Copy both the API Key and API Secret

### 2. Get Your LiveKit Server URL

Your LiveKit Cloud project URL will look like:
- `wss://your-project-name.livekit.cloud`

You can find this in your LiveKit Cloud dashboard under your project settings.

### 3. Configure Backend

Create or edit `backend/langgraph-voice-call-agent/.env`:

```env
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project-name.livekit.cloud
LIVEKIT_API_KEY=APIgCD5jBT47ogU
LIVEKIT_API_SECRET=your-api-secret-here

# OpenAI API Key (required for LangGraph agent)
OPENAI_API_KEY=your-openai-api-key

# Deepgram API Key (required for Speech-to-Text and Text-to-Speech)
DEEPGRAM_API_KEY=your-deepgram-api-key

# LangGraph Dev Server URL (optional; defaults to http://localhost:2024)
LANGGRAPH_URL=http://localhost:2024
```

**Replace:**
- `your-project-name.livekit.cloud` with your actual LiveKit Cloud URL
- `your-api-secret-here` with your LiveKit API Secret
- `your-openai-api-key` with your OpenAI API key
- `your-deepgram-api-key` with your Deepgram API key

### 4. Configure Frontend

Create or edit `frontend/langgraph-voice-call-agent-web/.env.local`:

```env
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project-name.livekit.cloud
LIVEKIT_API_KEY=APIgCD5jBT47ogU
LIVEKIT_API_SECRET=your-api-secret-here
```

**Replace:**
- `your-project-name.livekit.cloud` with your actual LiveKit Cloud URL (same as backend)
- `your-api-secret-here` with your LiveKit API Secret (same as backend)

### 5. Important Notes

- **Both frontend and backend must use the same LiveKit credentials**
- **Use `wss://` (secure WebSocket) for LiveKit Cloud, not `ws://`**
- **You don't need to run `docker compose` if using LiveKit Cloud** - the cloud service handles the server

## Quick Setup Commands

### Backend
```bash
cd backend/langgraph-voice-call-agent

# Create .env file (copy the template above and fill in your values)
# Then install and setup
uv sync
make download-files
```

### Frontend
```bash
cd frontend/langgraph-voice-call-agent-web

# Create .env.local file (copy the template above and fill in your values)
# Then install
npm install
```

## Verification

After setting up your `.env` files:

1. **Backend**: Start the agent and check logs for successful LiveKit connection
2. **Frontend**: Start the dev server and check browser console for connection errors
3. **Test**: Try connecting - you should see the agent join the room

## Troubleshooting

### "Invalid API key" errors
- Double-check your API Key and Secret are correct
- Ensure there are no extra spaces or quotes in your `.env` files
- Verify you're using the correct project's credentials

### "Cannot connect to LiveKit"
- Verify your `LIVEKIT_URL` uses `wss://` (not `ws://`)
- Check that your LiveKit Cloud project is active
- Ensure your API key has the correct permissions

### Connection works but agent doesn't respond
- Check backend agent logs for errors
- Verify LangGraph server is running
- Check that all API keys (OpenAI, Deepgram) are set correctly

## Next Steps

Once configured:
1. Start LangGraph server: `make langgraph-dev` (in backend directory)
2. Start backend agent: `make dev` (in backend directory)
3. Start frontend: `npm run dev` (in frontend directory)
4. Open `http://localhost:3000` and test!

See [QUICK_START.md](./QUICK_START.md) for the full startup sequence.

