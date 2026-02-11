# 🎙️ Building Voice AI Agents with LangGraph & LiveKit
## A Complete Beginner's Tutorial

Welcome! This tutorial will guide you through building a real-time voice AI agent from scratch. By the end, you'll understand how to connect LangGraph agents to voice streams, handle audio processing, and create a beautiful web interface.

---

## 📚 Table of Contents

1. [Understanding the Architecture](#1-understanding-the-architecture)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Frontend Deep Dive](#4-frontend-deep-dive)
5. [Putting It All Together](#5-putting-it-all-together)
6. [Customization & Extension](#6-customization--extension)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Understanding the Architecture

### What We're Building

A **real-time voice AI agent** that:
- Listens to your voice (Speech-to-Text)
- Processes your request with a LangGraph agent
- Responds with voice (Text-to-Speech)
- Maintains conversation context
- Works in both voice and text modes

### System Architecture

```
┌─────────────┐
│   Browser   │  ← User interacts here
│  (Frontend) │
└──────┬──────┘
       │ WebRTC
       ▼
┌─────────────────┐
│  LiveKit Server │  ← Real-time media routing
│  (Cloud/Local)  │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ LiveKit Agent│  │ LangGraph   │
│  (Backend)   │→ │   Server    │
│              │  │             │
│ • VAD        │  │ • AI Logic  │
│ • STT        │  │ • Tools     │
│ • TTS        │  │ • State     │
└──────────────┘  └──────────────┘
```

### Key Concepts

#### 1. **LiveKit** - Real-Time Communication
- Handles WebRTC connections
- Routes audio/video streams
- Manages rooms and participants
- Provides SDKs for easy integration

#### 2. **LangGraph** - AI Agent Framework
- Defines agent workflows (graphs)
- Manages conversation state
- Handles tool calls
- Supports streaming responses

#### 3. **Voice Pipeline Components**
- **VAD (Voice Activity Detection)**: Detects when you're speaking
- **STT (Speech-to-Text)**: Converts speech to text
- **TTS (Text-to-Speech)**: Converts text to speech
- **Turn Detection**: Knows when to stop listening and respond

#### 4. **Conversation State**
- Each conversation has a unique `thread_id`
- State persists across turns
- Allows context-aware responses

---

## 2. Prerequisites & Setup

### What You Need

1. **Python 3.12+** - For backend
2. **Node.js 18+** - For frontend
3. **API Keys**:
   - LiveKit (free tier available)
   - OpenAI (for LLM, STT, TTS)
4. **Basic Knowledge**:
   - Python basics
   - JavaScript/TypeScript basics
   - Terminal/command line

### Step 1: Clone the Project

```bash
git clone <your-repo-url>
cd langgraph-voice-back2front
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd backend/langgraph-voice-call-agent

# Install uv (fast Python package manager)
# Windows: pip install uv
# Mac/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
```

**Edit `.env` with your keys:**
```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI (for LLM, STT, TTS)
OPENAI_API_KEY=sk-your-key-here

# LangGraph Server
LANGGRAPH_URL=http://localhost:2024
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend
cd frontend/langgraph-voice-call-agent-web

# Install dependencies
npm install

# Create .env.local
cp .env.local.example .env.local
```

**Edit `.env.local`:**
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### Step 4: Verify Setup

```bash
# Test Python environment
cd backend/langgraph-voice-call-agent
uv run python --version  # Should show 3.12+

# Test Node.js
cd frontend/langgraph-voice-call-agent-web
node --version  # Should show 18+
```

---

## 3. Backend Deep Dive

### 3.1 Project Structure

```
backend/langgraph-voice-call-agent/
├── src/
│   ├── langgraph/
│   │   └── agent.py          # Your AI agent logic
│   └── livekit/
│       ├── agent.py          # LiveKit agent entrypoint
│       └── adapter/
│           └── langgraph.py  # Bridges LiveKit ↔ LangGraph
├── pyproject.toml            # Python dependencies
├── langgraph.json            # LangGraph config
└── .env                      # Environment variables
```

### 3.2 The LangGraph Agent (`src/langgraph/agent.py`)

**What it does:** Defines your AI agent's behavior, tools, and logic.

**Key Concepts:**

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# 1. Define tools (functions the agent can call)
def add_todo(task: str) -> str:
    """Add a new task to the todo list."""
    # Your tool logic here
    return f"Added: {task}"

# 2. Create the agent
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini"),
    tools=[add_todo, list_todos, complete_todo],
    prompt="You are a helpful assistant...",
    name="todo_agent"
)
```

**Understanding ReAct Agent:**
- **ReAct** = Reasoning + Acting
- Agent thinks about what to do, then acts (calls tools)
- Tools return results, agent processes and responds

**Exercise 1:** Add a new tool
1. Create a function `get_weather(city: str) -> str`
2. Add it to the `tools` list
3. Restart LangGraph server

### 3.3 The LiveKit Agent (`src/livekit/agent.py`)

**What it does:** Connects to LiveKit, processes audio, and calls your LangGraph agent.

**The Voice Pipeline:**

```python
session = AgentSession(
    vad=silero.VAD.load(),           # 1. Detect when user speaks
    stt=openai.STT(),                # 2. Convert speech → text
    llm=LangGraphAdapter(graph),     # 3. Process with LangGraph
    tts=openai.TTS(),                # 4. Convert text → speech
    turn_detection=None,              # 5. Use default endpointing
)
```

**Step-by-Step Flow:**

1. **VAD detects speech** → "User is speaking"
2. **STT transcribes** → "Hello, add a todo"
3. **LLM processes** → Calls `add_todo("Hello")`
4. **TTS synthesizes** → "Added todo: Hello"
5. **Audio sent back** → User hears response

**Understanding the Entrypoint:**

```python
async def entrypoint(ctx: JobContext):
    # 1. Connect to LiveKit room
    await ctx.connect()
    
    # 2. Wait for participant
    participant = await ctx.wait_for_participant()
    
    # 3. Get or create thread_id (conversation state)
    thread_id = participant.metadata or generate_new_id()
    
    # 4. Connect to LangGraph server
    graph = RemoteGraph("todo_agent", url="http://localhost:2024")
    
    # 5. Create agent session with voice pipeline
    session = AgentSession(vad=..., stt=..., llm=..., tts=...)
    
    # 6. Start processing
    await session.start(agent=VisionAssistant(), room=ctx.room)
```

**Exercise 2:** Modify the greeting
1. Find `session.say("Hey, I'm your...")`
2. Change the message
3. Restart the agent

### 3.4 The Adapter (`src/livekit/adapter/langgraph.py`)

**What it does:** Translates between LiveKit's LLM interface and LangGraph's streaming API.

**Key Challenge:** LiveKit expects a specific format, LangGraph uses a different one.

**How it works:**

```python
class LangGraphAdapter(llm.LLM):
    def chat(self, chat_ctx, tools, ...):
        # Create a stream that bridges the two systems
        return LangGraphStream(
            graph=self._graph,
            chat_ctx=chat_ctx,  # LiveKit format
            # Converts LiveKit messages → LangGraph state
            # Converts LangGraph responses → LiveKit chunks
        )
```

**Understanding Message Flow:**

```
LiveKit ChatContext → LangGraph State → LangGraph Stream → LiveKit ChatChunks
     (User input)         (messages)      (AI response)        (Audio output)
```

**Exercise 3:** Add logging
1. Add `logger.info()` statements in `_run()`
2. See how messages flow through the system

### 3.5 Running the Backend

**Terminal 1: LangGraph Server**
```bash
cd backend/langgraph-voice-call-agent
uv run langgraph dev
# Wait for: "LangGraph server running on http://localhost:2024"
```

**Terminal 2: LiveKit Agent**
```bash
cd backend/langgraph-voice-call-agent
uv run -m src.livekit.agent dev
# Wait for: "worker started" or "connecting to room"
```

**What's happening:**
- LangGraph server exposes your agent as an API
- LiveKit agent connects to LiveKit Cloud
- Agent waits for participants to join

---

## 4. Frontend Deep Dive

### 4.1 Project Structure

```
frontend/langgraph-voice-call-agent-web/
├── app/
│   ├── api/
│   │   └── connection-details/
│   │       └── route.ts        # Issues LiveKit tokens
│   ├── page.tsx                 # Main page
│   └── layout.tsx               # App layout
├── components/
│   ├── session-view.tsx         # Voice/text session UI
│   └── ...
├── hooks/
│   ├── useConnectionDetails.ts  # Gets LiveKit tokens
│   └── ...
└── .env.local                   # Frontend config
```

### 4.2 Connection Flow

**Step 1: Get Connection Details**

```typescript
// hooks/useConnectionDetails.ts
const response = await fetch('/api/connection-details', {
  method: 'POST',
  body: JSON.stringify({ room_config: { agents: [{ agent_name: 'todo_agent' }] } })
});

const { url, token, room } = await response.json();
```

**Step 2: Connect to LiveKit**

```typescript
// components/session-view.tsx
const room = new Room();
await room.connect(url, token);
```

**Step 3: Start Voice Call**

```typescript
// Enable microphone
await room.localParticipant.enableCameraAndMicrophone();

// Agent automatically joins when participant connects
```

### 4.3 Token Issuance (`app/api/connection-details/route.ts`)

**What it does:** Creates secure tokens for LiveKit connections.

**Key Code:**

```typescript
import { AccessToken } from 'livekit-server-sdk';

function createParticipantToken(userInfo, roomName, agentName) {
  const at = new AccessToken(API_KEY, API_SECRET, {
    identity: userInfo.identity,
    ttl: '15m',  // Token expires in 15 minutes
  });
  
  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });
  
  // Configure agent to join
  if (agentName) {
    at.roomConfig = new RoomConfiguration({
      agents: [{ agentName }],
    });
  }
  
  return at.toJwt();
}
```

**Security Note:** Never expose API secrets in frontend code. Always use a backend API route.

### 4.4 Dual-Mode UI

**Voice Mode:**
- Uses LiveKit SDK
- Full-duplex audio
- Real-time transcription
- Audio visualizations

**Text Mode:**
- Direct HTTP to LangGraph
- No LiveKit needed
- Simpler, faster
- Good for testing

**How it switches:**

```typescript
// app-config.ts
export const appConfig: AppConfig = {
  // ... other config
  // Mode is determined by which component is rendered
};

// components/session-view.tsx
const sessionMode = 'voice' | 'chat';  // Determines which mode
```

**Exercise 4:** Add a mode toggle
1. Add a button to switch between voice/chat
2. Conditionally render components based on mode

### 4.5 Running the Frontend

```bash
cd frontend/langgraph-voice-call-agent-web
npm run dev
# Open http://localhost:3000
```

**What you'll see:**
- Landing page with "Start Voice Call" button
- After clicking: Voice interface with microphone controls
- Real-time transcription appears as you speak

---

## 5. Putting It All Together

### Complete Startup Sequence

**Terminal 1: LangGraph Server**
```bash
cd backend/langgraph-voice-call-agent
uv run langgraph dev
```
✅ Wait for: `LangGraph server running on http://localhost:2024`

**Terminal 2: LiveKit Agent**
```bash
cd backend/langgraph-voice-call-agent
uv run -m src.livekit.agent dev
```
✅ Wait for: `worker started` or `connecting to room`

**Terminal 3: Frontend**
```bash
cd frontend/langgraph-voice-call-agent-web
npm run dev
```
✅ Open: http://localhost:3000

### Testing the Flow

1. **Open browser** → http://localhost:3000
2. **Click "Start Voice Call"**
3. **Allow microphone** when prompted
4. **Say:** "Add a todo: Learn voice AI"
5. **Listen:** Agent responds with confirmation
6. **Say:** "List my todos"
7. **Listen:** Agent reads back your todos

### Understanding What Happens

```
You speak → Browser captures audio
         → Sends to LiveKit server
         → LiveKit routes to agent
         → Agent: VAD → STT → LangGraph → TTS
         → Response sent back
         → You hear the response
```

**Timeline:**
- ~100-300ms: Audio capture → LiveKit
- ~200-500ms: STT processing
- ~500-2000ms: LangGraph processing (depends on complexity)
- ~200-500ms: TTS synthesis
- ~100-300ms: Audio playback
- **Total: ~1-3 seconds** for full round-trip

---

## 6. Customization & Extension

### 6.1 Customizing the Agent

**Change the System Prompt:**

```python
# src/langgraph/agent.py
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini"),
    tools=[...],
    prompt="""
    You are a helpful coding assistant.
    You help users write code, debug issues, and learn programming.
    Be concise but thorough.
    """,
    name="coding_agent"
)
```

**Add New Tools:**

```python
def search_web(query: str) -> str:
    """Search the web for information."""
    # Your implementation
    results = perform_search(query)
    return f"Found: {results}"

# Add to tools list
agent = create_react_agent(
    tools=[add_todo, search_web, ...],
    ...
)
```

**Change the Model:**

```python
# Use GPT-4 instead of GPT-4o-mini
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o"),  # More capable, slower
    ...
)
```

### 6.2 Customizing Voice Settings

**Change TTS Voice:**

```python
# src/livekit/agent.py
session = AgentSession(
    ...
    tts=openai.TTS(
        voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    ),
)
```

**Adjust Turn Detection:**

```python
session = AgentSession(
    ...
    min_endpointing_delay=0.5,  # Faster response (may cut off speech)
    max_endpointing_delay=8.0,  # Longer wait for slow speakers
)
```

### 6.3 Customizing the Frontend

**Change App Name:**

```typescript
// app-config.ts
export const appConfig: AppConfig = {
  appName: "My Voice Assistant",
  pageTitle: "Chat with My Assistant",
  ...
};
```

**Add Custom Styling:**

```typescript
// app/globals.css
:root {
  --primary-color: #your-color;
  --background: #your-bg;
}
```

**Add New Features:**

```typescript
// components/session-view.tsx
// Add a "Clear History" button
function handleClearHistory() {
  // Clear conversation state
}
```

### 6.4 Advanced: Multi-Agent System

**Create Multiple Agents:**

```python
# src/langgraph/agent.py
coding_agent = create_react_agent(...)
writing_agent = create_react_agent(...)
research_agent = create_react_agent(...)
```

**Route Based on Intent:**

```python
# Detect user intent, route to appropriate agent
if "code" in user_message.lower():
    agent = coding_agent
elif "write" in user_message.lower():
    agent = writing_agent
else:
    agent = research_agent
```

### 6.5 Advanced: Custom State Management

**Persist State to Database:**

```python
# Instead of in-memory todos
from sqlalchemy import create_engine
engine = create_engine("sqlite:///todos.db")

def add_todo(task: str) -> str:
    # Save to database
    with engine.connect() as conn:
        conn.execute(insert_todos, {"task": task})
    return f"Added: {task}"
```

**Use Redis for State:**

```python
import redis
r = redis.Redis()

def get_state(thread_id: str):
    return r.get(f"state:{thread_id}")
```

---

## 7. Troubleshooting

### Common Issues

#### "Cannot connect to LangGraph server"

**Symptoms:** Agent fails with connection error

**Solution:**
1. Check Terminal 1: Is LangGraph server running?
2. Check port 2024: `netstat -an | findstr 2024` (Windows) or `lsof -i :2024` (Mac/Linux)
3. Verify `LANGGRAPH_URL` in `.env`

#### "401 Unauthorized" from LiveKit

**Symptoms:** Frontend can't connect

**Solution:**
1. Check `.env.local` has correct `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`
2. Verify `LIVEKIT_URL` matches backend
3. Check token expiration (tokens expire after 15 minutes)

#### "Agent not responding"

**Symptoms:** You speak but no response

**Solution:**
1. Check Terminal 2: Are there errors?
2. Check microphone permissions in browser
3. Verify STT is working: Look for "received user transcript" in logs
4. Check LangGraph server is still running

#### "Models taking too long to load"

**Symptoms:** Agent startup is slow

**Solution:**
1. First run: Normal (models download)
2. Subsequent runs: Should be faster
3. If still slow: Check internet connection (models download from HuggingFace)

#### "Tool call errors"

**Symptoms:** `ValueError: Found AIMessages with tool_calls...`

**Solution:**
1. This is fixed in the latest code
2. Make sure you're using the updated `adapter/langgraph.py`
3. Restart both LangGraph server and agent

### Debugging Tips

**Enable Verbose Logging:**

```python
# src/livekit/agent.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Browser Console:**

```typescript
// Frontend logs show connection status
console.log("Room state:", room.state);
console.log("Participants:", room.participants);
```

**Monitor Network:**

- Open browser DevTools → Network tab
- Watch for WebSocket connections to LiveKit
- Check API calls to `/api/connection-details`

### Getting Help

1. **Check Logs:**
   - Terminal 1: LangGraph server logs
   - Terminal 2: Agent logs
   - Browser console: Frontend logs

2. **Verify Configuration:**
   - All `.env` files have correct values
   - API keys are valid
   - Ports are not in use

3. **Test Components Individually:**
   - Test LangGraph server: `curl http://localhost:2024/health`
   - Test LiveKit connection: Check browser console
   - Test agent: Look for "participant connected" in logs

---

## 🎓 Learning Path

### Beginner → Intermediate

1. ✅ **Complete this tutorial** - Understand the basics
2. **Modify the agent** - Add your own tools
3. **Customize the UI** - Make it your own
4. **Deploy to production** - Use LiveKit Cloud, deploy frontend

### Intermediate → Advanced

1. **Add multi-modal** - Process images/video
2. **Implement streaming** - Real-time partial responses
3. **Add authentication** - User accounts, sessions
4. **Scale horizontally** - Multiple agents, load balancing

### Advanced Topics

1. **Custom VAD models** - Train your own
2. **Voice cloning** - Custom TTS voices
3. **Multi-language** - Support multiple languages
4. **Analytics** - Track usage, performance

---

## 📚 Additional Resources

### Documentation
- [LiveKit Agents Docs](https://github.com/livekit/agents)
- [LangGraph Docs](https://github.com/langchain-ai/langgraph)
- [LiveKit SDK Docs](https://docs.livekit.io/)

### Examples
- [LiveKit Examples](https://github.com/livekit/agents/tree/main/examples)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

### Community
- [LiveKit Discord](https://discord.gg/livekit)
- [LangChain Discord](https://discord.gg/langchain)

---

## 🎉 Congratulations!

You now understand:
- ✅ How voice AI agents work
- ✅ How to connect LangGraph to LiveKit
- ✅ How to build a full-stack voice application
- ✅ How to customize and extend the system

**Next Steps:**
1. Build your own agent with custom tools
2. Deploy to production
3. Share your creation!

Happy building! 🚀

