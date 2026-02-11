# LangGraph Voice Agent - Full Stack

This repository contains both the frontend and backend for a real-time voice AI agent built with LangGraph and LiveKit.

## 🚀 Quick Start

**New to this project?** Start with [QUICK_START.md](./QUICK_START.md) for a 5-minute setup guide.

**Need detailed configuration?** See [SETUP.md](./SETUP.md) for comprehensive setup instructions.

## 📁 Project Structure

```
langgraph-voice-back2front/
├── backend/
│   └── langgraph-voice-call-agent/    # Python LiveKit agent + LangGraph
├── frontend/
│   └── langgraph-voice-call-agent-web/  # Next.js web interface
├── SETUP.md                            # Detailed setup guide
├── QUICK_START.md                      # Quick start guide
└── README.md                           # This file
```

## 🏗️ Architecture

```
Browser (Frontend)
    ↓ WebSocket
LiveKit Server (Real-time communication)
    ↑ WebSocket
Python Agent (Backend)
    ↓ HTTP
LangGraph Server (AI agent processing)
```

## 🔧 What You Need

1. **Docker** - For local LiveKit server
2. **Python 3.12+** with `uv` - For backend
3. **Node.js 18+** - For frontend
4. **API Keys**:
   - OpenAI (for LangGraph agent)
   - Deepgram (for speech-to-text/text-to-speech)

## 📋 Setup Checklist

- [ ] Install dependencies (backend: `uv sync`, frontend: `npm install`)
- [ ] Download models (`make download-files` in backend)
- [ ] Create `.env` files (copy from `.env.example` files)
- [ ] Add your API keys to backend `.env`
- [ ] Start LiveKit server (`docker compose up -d`)
- [ ] Start LangGraph server (`make langgraph-dev`)
- [ ] Start backend agent (`make dev`)
- [ ] Start frontend (`npm run dev`)
- [ ] Open `http://localhost:3000` and test!

## 🎯 Key Features

- **Real-time voice interaction** with LangGraph agents
- **Full-duplex communication** with low latency
- **Text chat support** alongside voice
- **Video/vision capabilities** (camera and screen sharing)
- **Modern web UI** with dark/light theme

## 📚 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Get running in 5 minutes
- **[SETUP.md](./SETUP.md)** - Detailed setup and configuration
- **Backend README**: `backend/langgraph-voice-call-agent/README.md`
- **Frontend README**: `frontend/langgraph-voice-call-agent-web/README.md`

## 🔗 Connection Flow

1. **Frontend** requests connection details from `/api/connection-details`
2. **API route** generates LiveKit access token
3. **Frontend** connects to LiveKit server via WebSocket
4. **Backend agent** (already connected) detects participant
5. **Backend agent** initializes voice session
6. **LangGraph server** processes conversation
7. **Backend** streams responses back through LiveKit
8. **Frontend** displays audio and transcriptions

## 🐛 Troubleshooting

### Common Issues

**Frontend can't connect:**
- Check LiveKit server is running: `docker compose ps`
- Verify `.env.local` has correct credentials
- Ensure backend and frontend use same LiveKit server

**Agent not responding:**
- Check backend agent terminal for errors
- Verify LangGraph server is running on port 2024
- Check API keys are set correctly

**Port conflicts:**
- Stop existing services: `docker compose down`
- Check ports 7880, 7881, 7882, 2024, 3000 are free

See [SETUP.md](./SETUP.md) for detailed troubleshooting.

## 🚢 Production Deployment

For production:
1. Use **LiveKit Cloud** instead of local Docker
2. Deploy backend agent to a server/cloud platform
3. Deploy frontend to Vercel/Netlify/etc.
4. Update environment variables with cloud credentials

See [SETUP.md](./SETUP.md) for production configuration.

## 📝 Environment Files

### Backend (`backend/langgraph-voice-call-agent/.env`)
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=your-key
DEEPGRAM_API_KEY=your-key
LANGGRAPH_URL=http://localhost:2024
```

### Frontend (`frontend/langgraph-voice-call-agent-web/.env.local`)
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

## 🤝 Contributing

This is a demonstration project. Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests
- Use as a reference for your own projects

## 📄 License

See individual LICENSE files in backend and frontend directories.

## 🙏 Acknowledgments

Inspired by [dqbd/langgraph-livekit-agents](https://github.com/dqbd/langgraph-livekit-agents).

---

**Ready to start?** → [QUICK_START.md](./QUICK_START.md)

