# 🔍 Deep Dive: What Happens When You Run `uv run -m src.livekit.agent dev`

This document explains **exactly** what happens at each step when you execute the agent command.

---

## 📋 Command Breakdown

```bash
uv run -m src.livekit.agent dev
```

**Breaking it down:**
- `uv run` - Runs a Python command using the `uv` package manager
- `-m src.livekit.agent` - Runs the Python module `src.livekit.agent` (which is `src/livekit/agent.py`)
- `dev` - The command argument passed to the module (development mode)

---

## 🚀 Execution Flow

### Phase 1: Python Module Loading

**Step 1.1: Module Resolution**
```
Python finds: backend/langgraph-voice-call-agent/src/livekit/agent.py
```

**Step 1.2: Import Execution**
```python
# These imports execute in order:

import logging
import os
import asyncio
import base64
from dotenv import load_dotenv  # ← Loads .env file

from langgraph.pregel.remote import RemoteGraph
from livekit.agents import Agent, AgentSession, get_job_context
from livekit.plugins import deepgram, silero, openai
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,  # ← This is the LiveKit CLI framework
    RoomInputOptions,
)
from livekit.agents.llm import ChatContext, ImageContent, ChatMessage
from livekit import rtc

from .adapter.langgraph import LangGraphAdapter  # ← Your custom adapter
```

**Step 1.3: Environment Loading**
```python
load_dotenv(dotenv_path=".env")  # ← Reads .env file
# Now these are available:
# - os.getenv("LIVEKIT_URL")
# - os.getenv("OPENAI_API_KEY")
# - etc.
```

**Step 1.4: Logger Setup**
```python
logger = logging.getLogger("voice-agent")
# Logger is ready to use
```

**Step 1.5: Module-Level Code**
```python
# These execute once when module loads:
TURN_DETECTOR_AVAILABLE = False
EnglishModel = None
# (Turn detector is disabled)
```

---

### Phase 2: CLI Framework Initialization

**Step 2.1: `if __name__ == "__main__"` Check**
```python
# Python checks: Is this being run as the main module?
# Answer: YES (because of `-m src.livekit.agent`)
# So this block executes:
```

**Step 2.2: `cli.run_app()` Call**
```python
cli.run_app(
    WorkerOptions(
        entrypoint_fnc=entrypoint,    # ← Function to call when participant joins
        prewarm_fnc=prewarm,          # ← Function to call during worker startup
    ),
)
```

**What `cli.run_app()` does:**
1. Parses command-line arguments (`dev` in this case)
2. Reads LiveKit configuration from environment
3. Connects to LiveKit server (Cloud or local)
4. Registers the worker with LiveKit
5. Sets up worker lifecycle management

---

### Phase 3: Worker Startup (Pre-Connection)

**Step 3.1: Worker Registration**
```
Agent connects to LiveKit server at: wss://your-project.livekit.cloud
Authenticates using: LIVEKIT_API_KEY and LIVEKIT_API_SECRET
Registers as: A worker that can handle voice agent jobs
```

**Step 3.2: `prewarm()` Execution**
```python
def prewarm(proc: JobProcess):
    """Called during worker initialization"""
    # Current implementation (lightweight):
    proc.userdata["vad"] = None  # ← Store None (models load later)
    logger.info("Skipping model preload to avoid initialization timeout...")
```

**What happens:**
- `prewarm()` is called **once** when the worker starts
- It's meant to preload models, but we skip it to avoid timeouts
- `proc.userdata` is a dictionary shared between `prewarm()` and `entrypoint()`
- Models will load on-demand in `entrypoint()` instead

**Step 3.3: Worker Ready**
```
Worker status: READY
Waiting for: Jobs from LiveKit server
Listening on: LiveKit server for room events
```

**At this point:**
- ✅ Worker is connected to LiveKit
- ✅ Worker is registered and ready
- ✅ No models loaded yet (they load when needed)
- ⏳ Waiting for a participant to join a room

---

### Phase 4: Waiting for Participants

**Step 4.1: LiveKit Job Queue**
```
LiveKit server maintains a queue of "jobs"
A job is created when:
  - A participant joins a room
  - The room is configured to use an agent (via room_config)
  - The agent name matches your worker's capabilities
```

**Step 4.2: Job Assignment**
```
When a participant joins:
  1. Frontend requests token with agent config:
     { room_config: { agents: [{ agent_name: "todo_agent" }] } }
  
  2. LiveKit server creates a job:
     - Room: "room-abc123"
     - Agent: "todo_agent"
     - Participant: "user-xyz"
  
  3. LiveKit assigns job to your worker:
     - Worker receives: "New job available"
     - Worker accepts: "I'll handle this"
```

**Step 4.3: Worker Spawns Process**
```
For each job, LiveKit creates a new process:
  - Isolated from other jobs
  - Has its own memory space
  - Can run concurrently with other jobs
```

---

### Phase 5: Entrypoint Execution (When Participant Joins)

**Step 5.1: `entrypoint()` Called**
```python
async def entrypoint(ctx: JobContext):
    # ctx contains:
    # - ctx.room: The LiveKit room
    # - ctx.proc: The job process (access to userdata from prewarm)
    # - ctx.connect(): Method to connect to the room
```

**Step 5.2: Connect to Room**
```python
logger.info(f"connecting to room {ctx.room.name}...")
await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
```

**What happens:**
- Agent connects to the LiveKit room as a participant
- `auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL` means:
  - Subscribe to all audio tracks (hear participants)
  - Subscribe to all video tracks (see participants)
  - Ready to publish audio (speak to participants)

**Step 5.3: Wait for Participant**
```python
participant = await ctx.wait_for_participant()
logger.info(f"participant: {participant}")
```

**What happens:**
- Agent waits for a human participant to join
- When someone joins, `participant` object is returned
- Contains: identity, name, metadata, etc.

**Step 5.4: Extract Thread ID**
```python
# Get thread_id from participant metadata (or use default)
thread_id = participant.metadata or "2432c116-7868-4d4a-8a87-189c58962dca"
# This thread_id is used to maintain conversation state in LangGraph
```

**Step 5.5: Verify LangGraph Server**
```python
langgraph_url = os.getenv("LANGGRAPH_URL", "http://localhost:2024")

# Health check
async with httpx.AsyncClient(timeout=2.0) as client:
    response = await client.get(f"{langgraph_url}/health")
    if response.status_code != 200:
        raise ConnectionError("LangGraph server not accessible")
```

**What happens:**
- Checks if LangGraph server is running
- If not accessible, raises error with helpful message
- Prevents agent from starting if LangGraph is down

**Step 5.6: Create RemoteGraph Client**
```python
graph = RemoteGraph("todo_agent", url=langgraph_url)
logger.info(f"Connected to LangGraph graph 'todo_agent' at {langgraph_url}")
```

**What happens:**
- Creates a client to communicate with LangGraph server
- `"todo_agent"` is the graph name (defined in `langgraph.json`)
- This client will make HTTP requests to LangGraph server

**Step 5.7: Load VAD Model**
```python
vad_model = ctx.proc.userdata.get("vad")  # From prewarm (currently None)
if vad_model is None:
    logger.info("VAD model not preloaded, loading now...")
    vad_model = silero.VAD.load()  # ← Downloads/loads model (first time only)
    ctx.proc.userdata["vad"] = vad_model  # Cache it
```

**What happens:**
- Checks if VAD was preloaded (it wasn't)
- Loads Silero VAD model (may download on first run)
- Caches it in `userdata` for reuse

**Step 5.8: Configure Turn Detection**
```python
turn_detector = None  # Disabled (we use default endpointing)
logger.info("Using default endpointing (turn detector disabled)")
```

**Step 5.9: Create Agent Session**
```python
session = AgentSession(
    vad=vad_model,                    # Voice Activity Detection
    stt=openai.STT(),                 # Speech-to-Text
    llm=LangGraphAdapter(             # Language Model (your agent)
        graph,
        config={"configurable": {"thread_id": thread_id}},
    ),
    tts=openai.TTS(),                 # Text-to-Speech
    turn_detection=turn_detector,     # Turn detection (None = default)
    min_endpointing_delay=0.8,        # Minimum wait before responding
    max_endpointing_delay=6.0,        # Maximum wait for slow speakers
)
```

**What this creates:**
- A complete voice pipeline
- Each component is wired together:
  ```
  Audio → VAD → STT → LLM → TTS → Audio
  ```

**Step 5.10: Create Vision Assistant**
```python
vision_agent = VisionAssistant()
vision_agent._room = ctx.room  # Give it room reference
```

**Step 5.11: Start Session**
```python
await session.start(
    agent=vision_agent,
    room=ctx.room,
    room_input_options=RoomInputOptions(
        video_enabled=True,
        audio_enabled=True,
        text_enabled=True
    )
)
```

**What happens:**
- Starts the voice pipeline
- Agent begins listening for audio
- VAD starts detecting speech
- Ready to process voice input

**Step 5.12: Initial Greeting**
```python
await session.say(
    "Hey, I'm your vision-enabled AI assistant!...",
    allow_interruptions=True,
)
```

**What happens:**
- Agent speaks the greeting
- `allow_interruptions=True` means user can interrupt mid-speech
- Audio is sent to participant through LiveKit

**Step 5.13: Main Loop**
```python
try:
    while True:
        await asyncio.sleep(1)  # Keep running
except KeyboardInterrupt:
    logger.info("Shutting down gracefully...")
finally:
    # Cleanup
    if hasattr(session.agent, 'cleanup'):
        await session.agent.cleanup()
```

**What happens:**
- Agent stays alive, processing voice input
- When user speaks, the pipeline activates:
  1. VAD detects speech
  2. STT transcribes to text
  3. LLM processes (calls LangGraph)
  4. TTS synthesizes response
  5. Audio sent back to user
- Loop continues until participant leaves or Ctrl+C

---

## 🔄 Real-Time Voice Processing Flow

Once the agent is running, here's what happens when you speak:

### Step-by-Step Voice Processing

```
1. You speak: "Add a todo: Learn voice AI"
   ↓
2. Browser captures audio → Sends to LiveKit server
   ↓
3. LiveKit routes audio → Agent receives audio track
   ↓
4. VAD detects: "User is speaking" (voice activity detected)
   ↓
5. STT processes: "Add a todo: Learn voice AI" (speech → text)
   ↓
6. LLM receives text → LangGraphAdapter processes:
   - Converts to LangGraph format
   - Sends to LangGraph server: POST /threads/{thread_id}/stream
   - LangGraph agent processes:
     * Calls add_todo("Learn voice AI")
     * Returns: "Added todo: Learn voice AI"
   ↓
7. TTS synthesizes: "Added todo: Learn voice AI" (text → speech)
   ↓
8. Audio sent back → LiveKit server → Browser → You hear response
```

**Timeline:**
- ~100-300ms: Audio capture & transmission
- ~200-500ms: STT processing
- ~500-2000ms: LangGraph processing (depends on complexity)
- ~200-500ms: TTS synthesis
- ~100-300ms: Audio playback
- **Total: ~1-3 seconds** for full round-trip

---

## 📊 Process Lifecycle

```
┌─────────────────────────────────────────┐
│ 1. Python Module Loads                 │
│    - Imports execute                    │
│    - .env file loaded                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 2. CLI Framework Initializes            │
│    - cli.run_app() called               │
│    - Connects to LiveKit server         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 3. Worker Startup                       │
│    - prewarm() called (lightweight)     │
│    - Worker registered with LiveKit     │
│    - Status: READY, waiting for jobs    │
└──────────────┬──────────────────────────┘
               │
               │ (Waits for participant)
               │
               ▼
┌─────────────────────────────────────────┐
│ 4. Participant Joins                   │
│    - LiveKit creates job                │
│    - Worker accepts job                 │
│    - New process spawned                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 5. Entrypoint Executes                  │
│    - Connects to room                   │
│    - Loads models (VAD, etc.)           │
│    - Creates voice pipeline             │
│    - Starts processing                  │
└──────────────┬──────────────────────────┘
               │
               │ (Processes voice in real-time)
               │
               ▼
┌─────────────────────────────────────────┐
│ 6. Participant Leaves / Ctrl+C         │
│    - Cleanup executed                   │
│    - Process terminates                 │
│    - Worker ready for next job          │
└─────────────────────────────────────────┘
```

---

## 🔑 Key Concepts

### Worker vs Process

- **Worker**: The main process that stays alive, connects to LiveKit, waits for jobs
- **Process**: A spawned process for each job (participant), runs `entrypoint()`, terminates when done

### Job Context

- `JobContext` (`ctx`) contains everything needed for a job:
  - `ctx.room`: The LiveKit room
  - `ctx.proc`: The process (access to `userdata`)
  - `ctx.connect()`: Method to connect to room

### Userdata

- `proc.userdata` is a dictionary shared between `prewarm()` and `entrypoint()`
- Used to cache models, configuration, etc.
- Persists for the lifetime of a job

### Thread ID

- Used to maintain conversation state in LangGraph
- Each conversation has a unique thread_id
- Can be passed via participant metadata
- LangGraph uses it to retrieve/update state

---

## 🐛 Debugging Tips

### Check Worker Status

```python
# In entrypoint(), add logging:
logger.info(f"Worker process ID: {os.getpid()}")
logger.info(f"Room: {ctx.room.name}")
logger.info(f"Participant: {participant.identity}")
```

### Monitor Model Loading

```python
# Check if VAD is loaded:
vad_loaded = ctx.proc.userdata.get("vad") is not None
logger.info(f"VAD loaded: {vad_loaded}")
```

### Verify LangGraph Connection

```python
# Test connection:
state = await graph.aget_state(config=self._llm._config)
logger.info(f"LangGraph state: {state}")
```

---

## 📝 Summary

When you run `uv run -m src.livekit.agent dev`:

1. **Module loads** → Imports, environment, logger setup
2. **CLI initializes** → `cli.run_app()` connects to LiveKit
3. **Worker starts** → `prewarm()` called, worker registered
4. **Waits for jobs** → Worker idle, listening for participants
5. **Participant joins** → Job created, process spawned
6. **Entrypoint runs** → Connects, loads models, creates pipeline
7. **Voice processing** → Real-time audio → text → AI → text → audio
8. **Cleanup** → When participant leaves or Ctrl+C

The agent is now ready to handle voice interactions! 🎉

