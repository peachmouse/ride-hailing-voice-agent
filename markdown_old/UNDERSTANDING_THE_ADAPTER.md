# 🔌 Understanding the Adapter

## What is the Adapter?

The **Adapter** (specifically `LangGraphAdapter`) is a **bridge** between two different systems that don't speak the same language:

- **LiveKit Agents** - Expects a specific LLM interface
- **LangGraph** - Uses a different API for streaming

The adapter translates between these two systems so they can work together.

---

## Why Do We Need an Adapter?

### The Problem: Two Different APIs

**LiveKit Agents expects:**
```python
class LLM:
    def chat(self, chat_ctx: ChatContext, tools: list, ...) -> LLMStream:
        # Returns a stream of ChatChunks
        # ChatChunks have: delta=ChoiceDelta(content="...")
```

**LangGraph provides:**
```python
graph.astream(
    input_state={"messages": [...]},
    stream_mode=["messages", "custom"]
)
# Returns: async iterator of (mode, data) tuples
# mode can be "messages" or "custom"
# data can be AIMessage, HumanMessage, etc.
```

**They're incompatible!** They use:
- Different data structures
- Different streaming formats
- Different message types

### The Solution: Adapter Pattern

The adapter implements LiveKit's `LLM` interface but internally uses LangGraph:

```python
class LangGraphAdapter(LLM):  # ← Implements LiveKit's LLM interface
    def chat(self, chat_ctx, tools, ...):
        # Convert LiveKit format → LangGraph format
        # Call LangGraph
        # Convert LangGraph format → LiveKit format
        return LangGraphStream(...)
```

---

## The Adapter's Two Main Functions

### 1. **Format Conversion** (LiveKit ↔ LangGraph)

#### Converting Input: LiveKit → LangGraph

**LiveKit sends:**
```python
ChatContext(
    items=[
        ChatMessage(role="user", content="Add a todo"),
        ChatMessage(role="assistant", content="I'll do that")
    ]
)
```

**Adapter converts to LangGraph format:**
```python
{
    "messages": [
        HumanMessage(content="Add a todo"),
        AIMessage(content="I'll do that")
    ]
}
```

**Code:**
```python
def _chat_ctx_to_state(self):
    messages = []
    for item in self._chat_ctx.items:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
    return {"messages": messages}
```

#### Converting Output: LangGraph → LiveKit

**LangGraph returns:**
```python
# From astream():
(mode="messages", data=[AIMessage(content="I've added the todo")])
```

**Adapter converts to LiveKit format:**
```python
ChatChunk(
    id="chunk_123",
    delta=ChoiceDelta(role="assistant", content="I've added the todo")
)
```

**Code:**
```python
async def _to_livekit_chunk(msg):
    if isinstance(msg, AIMessage):
        return ChatChunk(
            id=shortuuid(),
            delta=ChoiceDelta(role="assistant", content=msg.content)
        )
```

### 2. **Streaming Bridge** (Async Iterator Translation)

**LiveKit expects:**
```python
async for chunk in llm_stream:
    # chunk is a ChatChunk
    # Can be sent directly to TTS
```

**LangGraph provides:**
```python
async for mode, data in graph.astream(...):
    # mode is "messages" or "custom"
    # data is AIMessage, HumanMessage, or dict
```

**Adapter bridges:**
```python
class LangGraphStream(LLMStream):
    async def _run(self):
        # Get LangGraph stream
        async for mode, data in self._graph.astream(...):
            # Convert LangGraph format → LiveKit format
            chunk = await self._to_livekit_chunk(data[0])
            # Send to LiveKit
            self._event_ch.send_nowait(chunk)
```

---

## Complete Flow Through the Adapter

### Step-by-Step: User Says "Add a todo"

```
1. USER SPEAKS
   ↓
2. STT (Speech-to-Text)
   → "Add a todo: Buy milk"
   ↓
3. LIVEKIT FORMAT
   → ChatContext(items=[
        ChatMessage(role="user", content="Add a todo: Buy milk")
     ])
   ↓
4. ADAPTER: Convert Input
   → {"messages": [
        HumanMessage(content="Add a todo: Buy milk")
     ]}
   ↓
5. LANGGRAPH PROCESSING
   → graph.astream(input_state, ...)
   → Agent decides to call add_todo tool
   → Returns: AIMessage(tool_calls=[...])
   ↓
6. ADAPTER: Convert Output
   → ChatChunk(
        delta=ChoiceDelta(
            role="assistant",
            content="I'll add that to your todo list."
        )
     )
   ↓
7. LIVEKIT FORMAT
   → ChatChunk sent to TTS
   ↓
8. TTS (Text-to-Speech)
   → Audio: "I'll add that to your todo list."
   ↓
9. YOUR EARS
   → You hear the response
```

---

## Adapter Components

### 1. **LangGraphAdapter** (Main Class)

```python
class LangGraphAdapter(LLM):
    """Implements LiveKit's LLM interface"""
    
    def __init__(self, graph, config):
        self._graph = graph  # LangGraph RemoteGraph client
        self._config = config  # Thread ID, etc.
    
    def chat(self, chat_ctx, tools, ...):
        """LiveKit calls this - returns a stream"""
        return LangGraphStream(
            self,
            chat_ctx=chat_ctx,  # LiveKit format
            graph=self._graph,  # LangGraph client
            ...
        )
```

**Purpose:** Implements LiveKit's `LLM` interface so LiveKit can use it.

### 2. **LangGraphStream** (Streaming Bridge)

```python
class LangGraphStream(LLMStream):
    """Bridges LiveKit's LLMStream and LangGraph's astream"""
    
    async def _run(self):
        # 1. Convert LiveKit ChatContext → LangGraph state
        state = self._chat_ctx_to_state()
        
        # 2. Call LangGraph
        async for mode, data in self._graph.astream(state, ...):
            # 3. Convert LangGraph response → LiveKit ChatChunk
            chunk = await self._to_livekit_chunk(data[0])
            # 4. Send to LiveKit
            self._event_ch.send_nowait(chunk)
```

**Purpose:** Handles the actual streaming conversion.

### 3. **Conversion Methods**

#### `_chat_ctx_to_state()`
```python
def _chat_ctx_to_state(self):
    """Convert LiveKit ChatContext → LangGraph state"""
    messages = []
    for item in self._chat_ctx.items:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
    return {"messages": messages}
```

#### `_to_livekit_chunk()`
```python
async def _to_livekit_chunk(msg):
    """Convert LangGraph message → LiveKit ChatChunk"""
    if isinstance(msg, AIMessage):
        return ChatChunk(
            id=shortuuid(),
            delta=ChoiceDelta(role="assistant", content=msg.content)
        )
```

---

## Why Not Use LangGraph Directly?

### LiveKit Agents Framework Requirements

LiveKit Agents has a **specific architecture**:

```
AgentSession(
    vad=...,
    stt=...,      # Speech-to-Text
    llm=...,      # ← Must implement LLM interface
    tts=...,      # Text-to-Speech
)
```

The `llm` parameter **must** be an instance of `LLM` (LiveKit's interface). You can't just pass a LangGraph graph directly.

### The LLM Interface Contract

LiveKit's `LLM` interface requires:

```python
class LLM:
    def chat(
        self,
        chat_ctx: ChatContext,  # ← LiveKit format
        tools: list,
        ...
    ) -> LLMStream:  # ← Must return LLMStream
        ...
```

**LangGraph doesn't implement this interface**, so we need an adapter.

---

## Real-World Analogy

Think of the adapter like a **translator** at the UN:

- **LiveKit** speaks English (ChatContext, ChatChunk)
- **LangGraph** speaks French (messages, AIMessage)
- **Adapter** translates between them:
  - English → French (input)
  - French → English (output)

Without the adapter, they can't communicate!

---

## Key Responsibilities

### 1. **Message Format Conversion**
- LiveKit `ChatMessage` → LangChain `HumanMessage`/`AIMessage`
- LangChain `AIMessage` → LiveKit `ChatChunk`

### 2. **State Management**
- Maintains conversation state via `thread_id`
- Handles tool calls and ToolMessages
- Cleans up incomplete tool calls

### 3. **Streaming Translation**
- Converts LangGraph's `astream()` → LiveKit's `LLMStream`
- Handles different streaming modes ("messages", "custom")

### 4. **Error Handling**
- Handles LangGraph connection errors
- Manages incomplete tool calls
- Provides fallbacks

---

## Code Flow Example

### When User Speaks "List my todos"

```python
# 1. LiveKit calls adapter
stream = adapter.chat(
    chat_ctx=ChatContext(items=[...]),  # LiveKit format
    tools=[...]
)

# 2. Adapter creates stream
class LangGraphStream:
    async def _run(self):
        # 3. Convert LiveKit → LangGraph
        state = self._chat_ctx_to_state()
        # state = {"messages": [HumanMessage("List my todos")]}
        
        # 4. Call LangGraph
        async for mode, data in self._graph.astream(state, ...):
            # mode = "messages"
            # data = [AIMessage(tool_calls=[...])]
            
            # 5. Convert LangGraph → LiveKit
            chunk = await self._to_livekit_chunk(data[0])
            # chunk = ChatChunk(delta=ChoiceDelta(content="..."))
            
            # 6. Send to LiveKit
            self._event_ch.send_nowait(chunk)

# 7. LiveKit receives ChatChunk
# 8. TTS converts to audio
# 9. User hears response
```

---

## Benefits of the Adapter Pattern

### 1. **Separation of Concerns**
- LiveKit doesn't need to know about LangGraph
- LangGraph doesn't need to know about LiveKit
- Adapter handles the translation

### 2. **Flexibility**
- Can swap LangGraph for another system
- Can swap LiveKit for another framework
- Only need to change the adapter

### 3. **Reusability**
- Adapter can be used with any LangGraph agent
- Not tied to specific agent implementation

### 4. **Testability**
- Can test adapter independently
- Can mock LiveKit or LangGraph side

---

## Summary

**The Adapter is:**
- ✅ A **bridge** between LiveKit and LangGraph
- ✅ A **translator** that converts formats
- ✅ A **streaming converter** that handles async iterators
- ✅ A **state manager** that maintains conversation context

**Without the adapter:**
- ❌ LiveKit can't use LangGraph directly
- ❌ Format incompatibility
- ❌ No streaming translation
- ❌ Can't maintain conversation state

**With the adapter:**
- ✅ Seamless integration
- ✅ Format conversion handled
- ✅ Streaming works correctly
- ✅ Conversation state maintained

The adapter is the **glue** that makes everything work together! 🔌

