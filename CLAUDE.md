# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time voice AI agent: users talk to a LangGraph agent over LiveKit. Full-stack monorepo with a Python backend and a Next.js frontend.

## Repository Layout

- `backend/langgraph-voice-call-agent/` — Python LiveKit agent + LangGraph server
- `frontend/langgraph-voice-call-agent-web/` — Next.js 15 web interface (React 19, Tailwind 4)
- Root contains 30+ markdown docs (setup guides, walkthroughs, troubleshooting)

## Architecture

Four services run locally, communicating as follows:

```
Browser (Next.js :3000)
    ↕ WebSocket
LiveKit Server (Docker :7880)
    ↕ WebSocket
Python LiveKit Agent (:8030+)
    ↓ HTTP
LangGraph Server (:2024)
    ↓ HTTP
OpenAI API (LLM, STT, TTS)
```

**Audio pipeline:** Silero VAD → OpenAI STT → LangGraph LLM → OpenAI TTS

**Key adapter pattern:** `LangGraphAdapter` (`src/livekit/adapter/langgraph.py`) bridges LiveKit's `llm.LLM` interface to LangGraph's `RemoteGraph`. `LangGraphStream` consumes LangGraph's `astream()` output and converts it to LiveKit `ChatChunk` events. This is the most complex file in the codebase.

**Frontend modes:** Voice mode (full audio pipeline via LiveKit) and Chat mode (direct LangGraph SDK calls, no LiveKit agent involved).

**State continuity:** Thread IDs in participant metadata maintain conversation state across reconnects via LangGraph's checkpoint system.

## Development Commands

### Backend (from `backend/langgraph-voice-call-agent/`)

```bash
uv sync                          # Install Python dependencies
make download-files              # Download VAD and turn detection models
docker compose up -d             # Start local LiveKit server
make langgraph-dev               # Start LangGraph dev server (port 2024)
make dev                         # Start LiveKit voice agent
make dev-all                     # Start both LangGraph server + agent
make clean                       # Clean __pycache__ and generated files
```

Package manager: `uv`. Python 3.12+. Config in `pyproject.toml`.

### Frontend (from `frontend/langgraph-voice-call-agent-web/`)

```bash
npm install                      # Install dependencies
npm run dev                      # Dev server with Turbopack (port 3000)
npm run build                    # Production build
npm run lint                     # ESLint
npm run format                   # Prettier auto-format
npm run format:check             # Check formatting
```

Package manager: npm (pnpm 9.15.9 specified in package.json). Node.js 18+.

No test framework is configured for either backend or frontend.

## Key Files

| File | Role |
|------|------|
| `backend/.../src/livekit/agent.py` | Main entrypoint — connects to LiveKit, initializes VAD/STT/TTS pipeline, starts `VisionAssistant` session |
| `backend/.../src/livekit/adapter/langgraph.py` | `LangGraphAdapter` + `LangGraphStream` — bridges LiveKit ↔ LangGraph streaming, handles tool call errors and recovery |
| `backend/.../src/langgraph/agent.py` | Example ReAct agent (todo management) using `create_react_agent()` with gpt-4.1-nano |
| `backend/.../langgraph.json` | Registers LangGraph graphs (maps graph name → Python module path) |
| `backend/.../compose.yml` | Docker Compose for local LiveKit server (ports 7880, 7881, 7882/UDP) |
| `frontend/.../components/app.tsx` | Main app — manages LiveKit Room, session mode (chat/voice), connection lifecycle |
| `frontend/.../components/session-view.tsx` | Session UI — dual message sources (LiveKit for voice, LangGraph SDK for chat) |
| `frontend/.../app/api/connection-details/route.ts` | API endpoint that issues LiveKit access tokens (15-min TTL) |
| `frontend/.../app-config.ts` | Branding and feature flags (logo, colors, supported modes) |
| `frontend/.../hooks/useChatAndTranscription.ts` | Merges LiveKit chat messages with voice transcriptions |
| `frontend/.../hooks/useLangGraphChat.ts` | Direct LangGraph SDK integration for chat-only mode |

## Environment Variables

### Backend `.env`
`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `LANGGRAPH_URL`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`

### Frontend `.env.local`
`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `NEXT_PUBLIC_LANGGRAPH_API_URL` (optional), `NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID` (optional)

Dev defaults for LiveKit: `devkey` / `secret`.

## Important Patterns

- **RemoteGraph:** Backend connects to LangGraph server via HTTP, not in-process. This allows hot-reloading the agent graph without restarting the voice pipeline.
- **Incomplete tool call recovery:** `LangGraphStream._clean_incomplete_tool_calls()` strips orphaned tool calls from state when LangGraph returns errors, then retries with a fresh thread if needed.
- **VisionAssistant:** Extends LiveKit Agent to subscribe to video tracks (camera/screen share), capture frames, and inject visual context into LLM messages.
- **Frontend path alias:** `@/*` maps to the frontend root directory (tsconfig paths).
- **TypeScript strict mode** is enabled in the frontend.
