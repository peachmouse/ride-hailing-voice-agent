# FreeNow Ride-Hailing Voice Agent

AI-powered voice agent for booking rides and checking booking status. Built as a proof-of-concept for a ride-hailing app such as FreeNow by Lyft — demonstrating what an intelligent voice assistant can do that a traditional IVR cannot.

## What It Does

A user calls in (or opens the web interface) and speaks naturally:

> "I need a ride from Warsaw Central Station to the airport right now"

The agent extracts all booking details from a single utterance, confirms, estimates the fare, and books — no rigid menu trees, no "press 1 for pickup".

### Key Capabilities

- **Single-utterance slot extraction** — pickup, dropoff, and time from one sentence
- **Location disambiguation** — "the airport" prompts "Chopin or Modlin?"
- **Proactive fare estimates** — shares pricing before the user asks
- **Mid-flow changes** — "actually, pick me up at the Old Town instead" just works
- **Multi-intent handling** — "book a ride AND check my booking FN-12345"
- **Booking status tracking** — time-aware progression from confirmed through completed

## Architecture

```
Browser (Next.js :3000)
    ↕ WebSocket
LiveKit Server (Docker :7880)
    ↕ WebSocket
Python LiveKit Agent
    ↓ HTTP
LangGraph Server (:2024)
    ↓
Claude Sonnet 4.5 (reasoning + tool calls)
```

### Voice Stack

| Layer | Component | Role |
|-------|-----------|------|
| **Transport** | LiveKit | Real-time audio streaming between user and agent |
| **STT** | Deepgram Nova-3 | Speech-to-text with keyword boosting for domain terms |
| **Reasoning** | Claude Sonnet 4.5 via LangGraph | Slot extraction, disambiguation, and booking logic |
| **TTS** | Cartesia Sonic-2 | Text-to-speech with sub-100ms latency |

**Why these choices:**

- **Deepgram Nova-3** — lowest latency and highest accuracy for real-time streaming STT, with keyword boosting to improve recognition of FreeNow-specific terms.
- **Cartesia Sonic-2** — fastest time-to-first-audio of any production TTS, eliminating awkward pauses.
- **Claude Sonnet 4.5** — the reasoning that makes this more than an IVR: extracts multiple details from a single utterance, disambiguates locations, and adapts mid-conversation.
- **LiveKit** — WebRTC transport for this browser-based demo. In production, this layer would be replaced by Aircall or FreeNow's existing telephony infrastructure. The rest of the stack stays the same.

The architecture is deliberately modular: each layer can be replaced independently.

## Project Structure

```
backend/langgraph-voice-call-agent/
  src/langgraph/freenow_agent.py   # Agent logic, tools, and system prompt
  src/livekit/agent.py             # LiveKit voice pipeline (VAD, STT, TTS)
  src/livekit/adapter/langgraph.py # Bridges LiveKit ↔ LangGraph streaming
  langgraph.json                   # Registers the agent graph
  compose.yml                      # Docker Compose for local LiveKit server

frontend/langgraph-voice-call-agent-web/
  components/app.tsx               # Main app (LiveKit Room, session management)
  components/session-view.tsx      # Session UI (voice + chat modes)
  app-config.ts                    # Branding and feature flags
```

## Quick Start

### Prerequisites

- Python 3.12+, [uv](https://github.com/astral-sh/uv) package manager
- Node.js 18+
- Docker
- API keys: Anthropic, Deepgram, Cartesia, LiveKit

### Backend

```bash
cd backend/langgraph-voice-call-agent
cp .env.example .env               # Add your API keys
uv sync                            # Install dependencies
docker compose up -d               # Start local LiveKit server
make dev-all                       # Start LangGraph server + voice agent
```

### Frontend

```bash
cd frontend/langgraph-voice-call-agent-web
npm install
npm run dev                        # http://localhost:3000
```

Open **http://localhost:3000** and click **Start Voice Call** or **Start Chat**.

## Testing

### Test Scenarios

| # | Scenario | What to say | Expected |
|---|----------|-------------|----------|
| 1 | Single-utterance booking | "I need a ride from Warsaw Central Station to the airport right now" | Extracts all slots, confirms, books |
| 2 | Ambiguity resolution | "Take me to the airport" | Asks "Chopin or Modlin?" |
| 3 | Fare inquiry | "How much would a ride to Chopin Airport cost?" | Gives price range in PLN + duration |
| 4 | Mid-flow change | "Actually, change the pickup to the Old Town" | Updates without restarting |
| 5 | Multi-intent | "Book a ride and check booking FN-12345" | Handles both |
| 6 | Status check | "Check the status of booking FN-12345" | Reports current status |
| 7 | Off-topic recovery | "What's the weather like?" | Acknowledges, steers back |

### Voice Mode vs Chat Mode

- **Voice mode** — full pipeline (Deepgram STT → Claude → Cartesia TTS) via LiveKit. Tests the real voice experience.
- **Chat mode** — text-only, calls LangGraph directly. Faster for iterating on agent logic.

## Production Integration

The mock tools (`book_ride`, `estimate_fare`, `check_ride_status`, `get_nearby_locations`) would be replaced with real calls to internal microservices (via gRPC or message queues), making the agent a natural-language interface on top of existing booking, pricing, and dispatch infrastructure. LiveKit would be swapped for Aircall's telephony stack.
