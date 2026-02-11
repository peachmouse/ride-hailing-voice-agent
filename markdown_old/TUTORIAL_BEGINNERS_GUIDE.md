# 🎙️ Voice AI Agent Tutorial: Building with LangGraph & LiveKit

A comprehensive beginner's guide to building real-time voice AI agents using LangGraph and LiveKit.

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Understanding the Architecture](#understanding-the-architecture)
4. [Part 1: Backend Setup](#part-1-backend-setup)
5. [Part 2: Understanding the Audio Pipeline](#part-2-understanding-the-audio-pipeline)
6. [Part 3: LangGraph Integration](#part-3-langgraph-integration)
7. [Part 4: Frontend Setup](#part-4-frontend-setup)
8. [Part 5: Connecting Everything](#part-5-connecting-everything)
9. [Part 6: Customization](#part-6-customization)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

---

## Introduction

### What You'll Build

A **real-time voice AI agent** that:
- Listens to your voice in real-time
- Understands what you're saying (Speech-to-Text)
- Processes your request with an AI agent (LangGraph)
- Responds back with voice (Text-to-Speech)
- Maintains conversation context across turns

### Why This Stack?

- **LangGraph**: Powerful framework for building stateful AI agents with tools
- **LiveKit**: Real-time communication infrastructure (WebRTC) for low-latency voice
- **LiveKit Agents**: Python SDK that handles the complex audio pipeline
- **Next.js**: Modern React framework for the frontend

### What Makes This Different?

Unlike simple chatbots, this is a **full-duplex voice system**:
- ✅ Real-time audio streaming (not just text)
- ✅ Voice Activity Detection (knows when you're speaking)
- ✅ Turn detection (knows when to respond)
- ✅ Conversation state management
- ✅ Tool calling (agent can perform actions)

---

## Prerequisites

### Knowledge Requirements

**Beginner-friendly, but you should know:**
- Basic Python (functions, classes, async/await)
- Basic JavaScript/TypeScript (React components, hooks)
- Command line basics
- How to use a code editor

**Nice to have:**
- Understanding of WebRTC (we'll explain as we go)
- Experience with async programming
- Familiarity with REST APIs

### Tools You'll Need

1. **Python 3.12+** - [Download here](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download here](https://nodejs.org/)
3. **Git** - [Download here](https://git-scm.com/)
4. **Code Editor** - VS Code recommended
5. **API Keys** (we'll get these as we go):
   - OpenAI API key (for LLM, STT, TTS)
   - LiveKit credentials (free tier available)

### System Requirements

- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Internet**: Stable connection for API calls
- **Microphone**: For testing voice interactions

---

## Understanding the Architecture

### High-Level Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │◄───────►│  LiveKit     │◄───────►│   Backend    │
│  (Frontend) │  WebRTC │   Server     │  WebRTC │   Agent      │
└─────────────┘         └──────────────┘         └─────────────┘
                                                          │
                                                          ▼
                                                  ┌─────────────┐
                                                  │  LangGraph  │
                                                  │   Server    │
                                                  └─────────────┘
```

### Component Breakdown

#### 1. **Frontend (Browser)**
- **Role**: User interface and audio capture
- **Tech**: Next.js, React, LiveKit Web SDK
- **Responsibilities**:
  - Capture microphone audio
  - Display transcriptions
  - Play agent responses
  - Manage UI state

#### 2. **LiveKit Server**
- **Role**: Real-time communication hub
- **Tech**: LiveKit (self-hosted or cloud)
- **Responsibilities**:
  - WebRTC signaling and media routing
  - Room management
  - Participant coordination

#### 3. **Backend Agent**
- **Role**: Audio processing and AI logic
- **Tech**: Python, LiveKit Agents SDK
- **Responsibilities**:
  - Voice Activity Detection (VAD)
  - Speech-to-Text (STT)
  - Text-to-Speech (TTS)
  - Turn detection
  - LangGraph integration

#### 4. **LangGraph Server**
- **Role**: AI agent logic
- **Tech**: LangGraph, LangChain
- **Responsibilities**:
  - Conversation state management
  - Tool execution
  - LLM interactions

### Data Flow

```
User speaks
    ↓
Frontend captures audio
    ↓
LiveKit routes audio to Backend Agent
    ↓
Backend: VAD detects speech
    ↓
Backend: STT converts speech → text
    ↓
Backend: Sends text to LangGraph
    ↓
LangGraph: Processes with LLM + tools
    ↓
LangGraph: Returns response text
    ↓
Backend: TTS converts text → audio
    ↓
Backend: Sends audio to LiveKit
    ↓
LiveKit routes audio to Frontend
    ↓
Frontend plays audio to user
```

---

## Part 1: Backend Setup

### Step 1.1: Project Structure

```
langgraph-voice-call-agent/
├── src/
│   ├── langgraph/
│   │   └── agent.py          # Your AI agent logic
│   └── livekit/
│       ├── agent.py          # LiveKit agent entrypoint
│       └── adapter/
│           └── langgraph.py  # Bridges LiveKit ↔ LangGraph
├── pyproject.toml            # Python dependencies
├── langgraph.json           # LangGraph server config
└── .env                     # Environment variables
```

### Step 1.2: Understanding the Backend Components

#### `src/langgraph/agent.py` - Your AI Agent

This is where you define **what your agent can do**:

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Define tools (functions your agent can call)
def add_todo(task: str) -> str:
    """Add a task to the todo list."""
    # ... implementation
    return f"Added: {task}"

# Create the agent
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4"),
    tools=[add_todo, list_todos, complete_todo],
    name="todo_agent"
)
```

**Key Concepts:**
- **Tools**: Functions the agent can call (like `add_todo`)
- **ReAct Agent**: A pattern where the agent reasons and acts
- **State**: Conversation history maintained by LangGraph

#### `src/livekit/agent.py` - Audio Pipeline

This connects your agent to voice:

```python
from livekit.agents import AgentSession
from livekit.plugins import silero, openai

session = AgentSession(
    vad=silero.VAD.load(),           # Detects when user is speaking
    stt=openai.STT(),                # Converts speech → text
    llm=LangGraphAdapter(graph),     # Your LangGraph agent
    tts=openai.TTS(),                # Converts text → speech
)
```

**Key Concepts:**
- **VAD (Voice Activity Detection)**: Knows when you're speaking
- **STT (Speech-to-Text)**: Converts your speech to text
- **TTS (Text-to-Speech)**: Converts agent's text to speech
- **Turn Detection**: Knows when to start/stop listening

#### `src/livekit/adapter/langgraph.py` - The Bridge

This connects LiveKit's LLM interface to LangGraph:

```python
class LangGraphAdapter(llm.LLM):
    """Makes LangGraph look like a LiveKit LLM."""
    
    def chat(self, chat_ctx, tools, ...):
        # Converts LiveKit messages → LangGraph state
        # Streams LangGraph responses → LiveKit chunks
        return LangGraphStream(...)
```

**Key Concepts:**
- **Adapter Pattern**: Makes two different interfaces work together
- **Streaming**: Real-time responses, not waiting for complete answers

### Step 1.3: Setting Up Dependencies

**File: `pyproject.toml`**

```toml
[project]
name = "langgraph-voice-call-agent"
requires-python = ">=3.12"
dependencies = [
    "langchain>=0.3.27",
    "langchain-openai>=0.3.30",
    "langgraph>=0.6.6",
    "langgraph-cli[inmem]>=0.3.8",
    "livekit>=1.0.12",
    "livekit-agents[openai,silero]~=1.2",
    "livekit-plugins-openai>=1.2.6",
    "livekit-plugins-silero>=1.2.6",
    "python-dotenv>=1.1.1",
]
```

**Install:**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Step 1.4: Environment Variables

**File: `.env`**

```env
# OpenAI (for LLM, STT, TTS)
OPENAI_API_KEY=sk-your-key-here

# LiveKit (for real-time communication)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# LangGraph (optional, defaults to localhost:2024)
LANGGRAPH_URL=http://localhost:2024
```

**Getting API Keys:**
1. **OpenAI**: https://platform.openai.com/api-keys
2. **LiveKit Cloud**: https://cloud.livekit.io (free tier available)

---

## Part 2: Understanding the Audio Pipeline

### Step 2.1: Voice Activity Detection (VAD)

**What it does:** Detects when the user is speaking (not just noise)

```python
vad = silero.VAD.load()
# VAD analyzes audio chunks
# Returns: True if speech detected, False otherwise
```

**Why it matters:**
- Saves API costs (only processes when you're speaking)
- Reduces false triggers
- Better user experience

**How it works:**
1. Audio comes in as chunks (small pieces)
2. VAD analyzes each chunk
3. If speech detected → send to STT
4. If silence → wait

### Step 2.2: Speech-to-Text (STT)

**What it does:** Converts your spoken words into text

```python
stt = openai.STT()  # Or Deepgram, etc.
# Audio → "Hello, how are you?"
```

**Providers:**
- **OpenAI Whisper**: Good quality, reliable
- **Deepgram**: Fast, good for real-time
- **Google Speech-to-Text**: Alternative option

**How it works:**
1. Receives audio chunks (when VAD detects speech)
2. Sends to STT API
3. Receives transcribed text
4. Passes text to LangGraph agent

### Step 2.3: Text-to-Speech (TTS)

**What it does:** Converts agent's text response into speech

```python
tts = openai.TTS()  # Or Deepgram, etc.
# "I can help you with that!" → Audio
```

**Providers:**
- **OpenAI TTS**: Natural voices, good quality
- **Deepgram TTS**: Fast, good for real-time
- **ElevenLabs**: Very natural, premium option

**How it works:**
1. Agent generates text response
2. Sends text to TTS API
3. Receives audio stream
4. Sends audio to user via LiveKit

### Step 2.4: Turn Detection

**What it does:** Knows when you've finished speaking and when to respond

```python
session = AgentSession(
    min_endpointing_delay=0.8,  # Wait 0.8s of silence before responding
    max_endpointing_delay=6.0,  # Max wait time
)
```

**Why it matters:**
- Prevents cutting off mid-sentence
- Natural conversation flow
- Handles pauses and "um"s

**How it works:**
1. User starts speaking → VAD detects
2. User pauses → Wait for `min_endpointing_delay`
3. If silence continues → End turn, process
4. If user speaks again → Continue listening

---

## Part 3: LangGraph Integration

### Step 3.1: Understanding LangGraph

**LangGraph** is a framework for building **stateful AI agents**.

**Key Concepts:**

1. **Graph**: A workflow of nodes (steps)
2. **State**: Conversation history and data
3. **Nodes**: Functions that process state
4. **Edges**: Connections between nodes
5. **Tools**: Functions the agent can call

### Step 3.2: Creating Your Agent

**File: `src/langgraph/agent.py`**

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Define a tool
def add_todo(task: str) -> str:
    """Add a task to the todo list."""
    todos.append({"task": task, "completed": False})
    return f"Added: {task}"

# Create ReAct agent (Reasoning + Acting)
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4"),
    tools=[add_todo],
    name="todo_agent"
)
```

**What's happening:**
1. **ReAct Pattern**: Agent reasons about what to do, then acts
2. **Tool Calling**: Agent can call functions (tools)
3. **State Management**: LangGraph maintains conversation history

### Step 3.3: Understanding the ReAct Pattern

**ReAct = Reasoning + Acting**

```
User: "Add buy groceries to my todo list"
    ↓
Agent thinks: "I need to call add_todo tool"
    ↓
Agent calls: add_todo("buy groceries")
    ↓
Tool returns: "Added: buy groceries"
    ↓
Agent responds: "I've added 'buy groceries' to your todo list"
```

### Step 3.4: State Management

**LangGraph maintains state automatically:**

```python
# Each conversation has a thread_id
config = {"configurable": {"thread_id": "user-123"}}

# LangGraph stores:
# - All messages (user, assistant, tool)
# - Tool call results
# - Conversation context
```

**Why this matters:**
- Agent remembers previous messages
- Context persists across turns
- Tool results are available for future turns

### Step 3.5: Running LangGraph Server

**File: `langgraph.json`**

```json
{
  "graphs": {
    "todo_agent": "./src/langgraph/agent.py:agent"
  },
  "env": ".env"
}
```

**Start server:**
```bash
uv run langgraph dev
# Server runs on http://localhost:2024
```

**What it does:**
- Exposes your agent as a REST API
- Handles state management
- Processes tool calls
- Streams responses

---

## Part 4: Frontend Setup

### Step 4.1: Project Structure

```
langgraph-voice-call-agent-web/
├── app/
│   ├── api/
│   │   └── connection-details/
│   │       └── route.ts        # Issues LiveKit tokens
│   └── page.tsx                 # Main UI
├── components/
│   ├── session-view.tsx         # Voice call UI
│   └── provider.tsx            # LiveKit context
├── hooks/
│   ├── useConnectionDetails.ts  # Gets LiveKit credentials
│   └── useVoiceAssistant.ts    # Voice assistant logic
└── .env.local                  # Environment variables
```

### Step 4.2: Understanding the Frontend Components

#### `app/api/connection-details/route.ts` - Token Issuance

**What it does:** Creates secure tokens for LiveKit connection

```typescript
export async function POST(req: Request) {
  // Get LiveKit credentials
  const API_KEY = process.env.LIVEKIT_API_KEY;
  const API_SECRET = process.env.LIVEKIT_API_SECRET;
  
  // Create participant token
  const token = await createParticipantToken(
    { identity: "user-123", name: "User" },
    roomName,
    agentName
  );
  
  return Response.json({ token, url, roomName });
}
```

**Why it matters:**
- Security: Tokens expire and are scoped
- Authentication: Only authorized users can connect
- Room configuration: Can specify which agent to use

#### `components/session-view.tsx` - Main UI

**What it does:** Manages the voice call interface

```typescript
export const SessionView = ({ sessionMode }) => {
  const { state } = useVoiceAssistant();
  const room = useRoomContext();
  
  // Connect to LiveKit room
  // Display transcriptions
  // Show audio visualizations
  // Handle user interactions
}
```

**Features:**
- Real-time transcription display
- Audio level visualizations
- Chat interface
- Connection status

#### `hooks/useConnectionDetails.ts` - Connection Management

**What it does:** Fetches LiveKit connection details

```typescript
export function useConnectionDetails() {
  const [details, setDetails] = useState(null);
  
  // Fetch from /api/connection-details
  // Refresh token when needed
  // Return connection info
}
```

### Step 4.3: Setting Up the Frontend

**Install dependencies:**
```bash
cd frontend/langgraph-voice-call-agent-web
npm install
```

**Environment variables:**
```env
# .env.local
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

**Start development server:**
```bash
npm run dev
# Runs on http://localhost:3000
```

---

## Part 5: Connecting Everything

### Step 5.1: The Complete Flow

**Starting the system (3 terminals):**

**Terminal 1: LangGraph Server**
```bash
cd backend/langgraph-voice-call-agent
uv run langgraph dev
# ✅ Wait for: "LangGraph server running on http://localhost:2024"
```

**Terminal 2: Backend Agent**
```bash
cd backend/langgraph-voice-call-agent
uv run -m src.livekit.agent dev
# ✅ Wait for: "worker started" or "connecting to room"
```

**Terminal 3: Frontend**
```bash
cd frontend/langgraph-voice-call-agent-web
npm run dev
# ✅ Wait for: "Ready on http://localhost:3000"
```

### Step 5.2: Testing the Connection

1. **Open browser:** http://localhost:3000
2. **Click:** "Start Voice Call"
3. **Allow microphone access**
4. **Speak:** "Hello, can you help me?"
5. **Listen:** Agent should respond

### Step 5.3: Understanding What Happens

**When you speak:**

```
1. Browser captures audio
   ↓
2. Frontend sends audio to LiveKit
   ↓
3. LiveKit routes to Backend Agent
   ↓
4. Backend: VAD detects speech
   ↓
5. Backend: STT converts to text
   ↓
6. Backend: Sends text to LangGraph
   ↓
7. LangGraph: Processes with LLM
   ↓
8. LangGraph: Returns response
   ↓
9. Backend: TTS converts to audio
   ↓
10. Backend: Sends audio to LiveKit
   ↓
11. LiveKit routes to Frontend
   ↓
12. Browser plays audio
```

### Step 5.4: Debugging Tips

**Check each component:**

1. **LangGraph Server:**
   - Look for: "LangGraph server running"
   - Test: `curl http://localhost:2024/health`

2. **Backend Agent:**
   - Look for: "LangGraph server is accessible"
   - Look for: "connecting to room"
   - Check for errors in logs

3. **Frontend:**
   - Check browser console (F12)
   - Look for: "Connected to room"
   - Check network tab for API calls

---

## Part 6: Customization

### Step 6.1: Customizing Your Agent

**Add more tools:**

```python
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation
    return results

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4"),
    tools=[add_todo, search_web, send_email],
    name="assistant_agent"
)
```

**Change the model:**

```python
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o"),  # Different model
    tools=[...],
)
```

**Customize the prompt:**

```python
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4"),
    tools=[...],
    prompt="You are a helpful assistant that...",
)
```

### Step 6.2: Customizing the Audio Pipeline

**Change STT provider:**

```python
# From OpenAI to Deepgram
from livekit.plugins import deepgram

stt = deepgram.STT(
    model="nova-2",
    language="en-US",
    api_key=os.getenv("DEEPGRAM_API_KEY"),
)
```

**Change TTS voice:**

```python
tts = openai.TTS(
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
)
```

**Adjust turn detection:**

```python
session = AgentSession(
    min_endpointing_delay=1.0,  # Wait longer before responding
    max_endpointing_delay=8.0,  # Allow longer pauses
)
```

### Step 6.3: Customizing the Frontend

**Change UI theme:**

```typescript
// app-config.ts
export const appConfig = {
  theme: "dark",  // or "light"
  // ... other config
}
```

**Add features:**

```typescript
// Add video support
<VideoTrack track={videoTrack} />

// Add screen sharing
room.localParticipant.setScreenShareEnabled(true)
```

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to LangGraph server"

**Problem:** LangGraph server not running

**Solution:**
```bash
# Make sure Terminal 1 has:
uv run langgraph dev
# And shows: "LangGraph server running on http://localhost:2024"
```

#### 2. "401 Unauthorized" from API

**Problem:** Invalid API key

**Solution:**
- Check `.env` file has correct keys
- Verify keys are active in provider dashboard
- Make sure no extra spaces in keys

#### 3. "Agent not responding"

**Problem:** Multiple possible causes

**Checklist:**
- ✅ LangGraph server running?
- ✅ Backend agent connected?
- ✅ Frontend connected to room?
- ✅ Microphone permissions granted?
- ✅ Check browser console for errors

#### 4. "Models taking too long to load"

**Problem:** First-time model download

**Solution:**
- This is normal on first run (2-5 minutes)
- Models are cached after first download
- Subsequent runs are faster

#### 5. "Connection timeout"

**Problem:** Network or firewall issues

**Solution:**
- Check internet connection
- Verify LiveKit URL is correct
- Check firewall settings
- Try using LiveKit Cloud instead of self-hosted

---

## Next Steps

### Learning Path

1. **Understand the basics:**
   - ✅ How audio flows through the system
   - ✅ How LangGraph manages state
   - ✅ How LiveKit handles real-time communication

2. **Experiment:**
   - Add new tools to your agent
   - Try different STT/TTS providers
   - Customize the UI

3. **Build something:**
   - Create a domain-specific agent (e.g., customer support)
   - Add video capabilities
   - Integrate with external APIs

4. **Optimize:**
   - Reduce latency
   - Improve accuracy
   - Add error handling
   - Scale for production

### Resources

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **LiveKit Docs:** https://docs.livekit.io/
- **LiveKit Agents:** https://github.com/livekit/agents
- **LangChain Docs:** https://python.langchain.com/

### Advanced Topics

- **Custom Graph Nodes:** Build complex workflows
- **Streaming Responses:** Real-time partial responses
- **Multi-modal:** Add image/video understanding
- **Production Deployment:** Docker, Kubernetes, scaling
- **Monitoring:** Logging, metrics, error tracking

---

## Summary

You've learned:

1. ✅ **Architecture**: How all components fit together
2. ✅ **Backend**: Audio pipeline and LangGraph integration
3. ✅ **Frontend**: Real-time UI with LiveKit
4. ✅ **Connection**: How everything communicates
5. ✅ **Customization**: How to extend and modify

**You now have a solid foundation for building voice AI agents!** 🎉

Keep experimenting, building, and learning. The voice AI space is rapidly evolving, and you're now equipped to participate in it.

