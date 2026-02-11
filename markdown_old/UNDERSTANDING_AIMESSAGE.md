# 🤖 Understanding AIMessage

## What is an AIMessage?

An **`AIMessage`** is a LangChain/LangGraph class that represents a message from the AI assistant (the agent) in a conversation.

### Basic Definition

```python
from langchain_core.messages import AIMessage

# A simple AI message
message = AIMessage(content="Hello! How can I help you?")
```

**Key Points:**
- It's a **message object** that represents what the AI said
- It's part of LangChain's message system for conversation management
- It's used to maintain conversation history

---

## Message Types in LangChain

LangChain uses different message types to represent different roles in a conversation:

### 1. **HumanMessage** - What the user said
```python
from langchain_core.messages import HumanMessage

user_msg = HumanMessage(content="Add a todo: Buy groceries")
# Represents: User said "Add a todo: Buy groceries"
```

### 2. **AIMessage** - What the AI said
```python
from langchain_core.messages import AIMessage

ai_msg = AIMessage(content="I've added 'Buy groceries' to your todo list.")
# Represents: AI said "I've added 'Buy groceries' to your todo list."
```

### 3. **SystemMessage** - System instructions
```python
from langchain_core.messages import SystemMessage

system_msg = SystemMessage(content="You are a helpful todo list assistant.")
# Represents: System instruction for the AI
```

### 4. **ToolMessage** - Tool execution results
```python
from langchain_core.messages import ToolMessage

tool_msg = ToolMessage(
    content="Added todo: Buy groceries",
    tool_call_id="call_abc123"
)
# Represents: Result from calling a tool (function)
```

---

## AIMessage with Tool Calls

An `AIMessage` can contain **tool calls** - requests from the AI to execute functions.

### Simple AIMessage (No Tools)
```python
AIMessage(content="Hello! How can I help you?")
```

### AIMessage with Tool Calls
```python
AIMessage(
    content="I'll add that to your todo list.",
    tool_calls=[
        {
            "name": "add_todo",
            "args": {"task": "Buy groceries"},
            "id": "call_abc123",
            "type": "tool_call"
        }
    ]
)
```

**What this means:**
- The AI wants to call the `add_todo` tool
- It's passing `{"task": "Buy groceries"}` as arguments
- The tool call has an ID: `"call_abc123"`

### Complete Tool Call Flow

```
1. User: "Add a todo: Buy groceries"
   → HumanMessage(content="Add a todo: Buy groceries")

2. AI decides to call tool:
   → AIMessage(
        content="I'll add that to your todo list.",
        tool_calls=[{
            "name": "add_todo",
            "args": {"task": "Buy groceries"},
            "id": "call_abc123"
        }]
     )

3. Tool executes:
   → ToolMessage(
        content="Added todo: Buy groceries",
        tool_call_id="call_abc123"  ← Matches the tool call ID
     )

4. AI responds with result:
   → AIMessage(content="I've added 'Buy groceries' to your todo list.")
```

---

## Why Tool Calls Must Have ToolMessages

**The Rule:** Every `AIMessage` with `tool_calls` MUST have corresponding `ToolMessage` objects.

### ✅ Valid State
```python
messages = [
    HumanMessage(content="Delete todo 2"),
    AIMessage(
        content="I'll delete that for you.",
        tool_calls=[{"name": "delete_todo", "args": {"todo_id": 2}, "id": "call_123"}]
    ),
    ToolMessage(
        content="Deleted todo #2",
        tool_call_id="call_123"  ← Matches the tool call ID
    )
]
```

### ❌ Invalid State (Causes Error)
```python
messages = [
    HumanMessage(content="Delete todo 2"),
    AIMessage(
        content="I'll delete that for you.",
        tool_calls=[{"name": "delete_todo", "args": {"todo_id": 2}, "id": "call_123"}]
    )
    # Missing ToolMessage! ← This causes the error you saw
]
```

**Why this matters:**
- LLM providers (OpenAI, etc.) require complete tool call pairs
- The AI needs to see the tool result to continue the conversation
- Incomplete tool calls break conversation flow

---

## How AIMessage is Used in This Project

### 1. In the Adapter (`src/livekit/adapter/langgraph.py`)

**Converting LiveKit messages to LangChain messages:**
```python
def _chat_ctx_to_state(self):
    messages = []
    for item in self._chat_ctx.items:
        if item.role == "assistant":
            # Convert LiveKit assistant message to AIMessage
            messages.append(AIMessage(content=item.text_content))
        elif item.role == "user":
            # Convert LiveKit user message to HumanMessage
            messages.append(HumanMessage(content=item.text_content))
    
    return {"messages": messages}
```

**Converting LangGraph responses to LiveKit chunks:**
```python
async def _to_livekit_chunk(msg):
    if isinstance(msg, AIMessage):
        # Extract content from AIMessage
        content = msg.content
        # Convert to LiveKit ChatChunk for audio synthesis
        return ChatChunk(delta=ChoiceDelta(content=content))
```

### 2. In the LangGraph Agent (`src/langgraph/agent.py`)

The agent creates `AIMessage` objects when it responds:

```python
# When the agent responds, LangGraph creates:
AIMessage(content="Here are your todos: ...")

# When the agent calls a tool, LangGraph creates:
AIMessage(
    content="I'll do that for you.",
    tool_calls=[{"name": "add_todo", "args": {...}, "id": "..."}]
)
```

### 3. In Conversation State

The conversation state is a list of messages:

```python
state = {
    "messages": [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Add a todo: Learn Python"),
        AIMessage(
            content="I'll add that for you.",
            tool_calls=[{"name": "add_todo", ...}]
        ),
        ToolMessage(content="Added todo: Learn Python", tool_call_id="..."),
        AIMessage(content="I've added 'Learn Python' to your todo list.")
    ]
}
```

---

## AIMessage Properties

### Common Properties

```python
message = AIMessage(
    content="Hello!",
    id="msg_123",  # Optional: unique message ID
    tool_calls=[...],  # Optional: tool calls
    response_metadata={...}  # Optional: metadata
)

# Access properties
print(message.content)  # "Hello!"
print(message.tool_calls)  # [{"name": "...", ...}]
print(message.id)  # "msg_123"
```

### Tool Calls Structure

```python
tool_calls = [
    {
        "name": "add_todo",  # Function name
        "args": {"task": "Buy milk"},  # Function arguments
        "id": "call_abc123",  # Unique call ID
        "type": "tool_call"  # Message type
    }
]
```

---

## Real Example from Your Project

### Scenario: User asks to list todos

**1. User speaks:** "List my todos"
```
→ STT converts to text
→ HumanMessage(content="List my todos")
```

**2. Agent processes:**
```python
# LangGraph agent decides to call list_todos tool
AIMessage(
    content="Let me check your todos.",
    tool_calls=[{
        "name": "list_todos",
        "args": {},
        "id": "call_list_123"
    }]
)
```

**3. Tool executes:**
```python
# list_todos() returns: [{"id": 1, "task": "Buy milk", ...}]
ToolMessage(
    content="[{'id': 1, 'task': 'Buy milk', ...}]",
    tool_call_id="call_list_123"  # Matches the tool call ID
)
```

**4. Agent responds:**
```python
# Agent processes tool result and responds
AIMessage(content="Here are your todos:\n1. Buy milk\n...")
```

**5. TTS converts to speech:**
```
→ "Here are your todos: 1. Buy milk..."
→ User hears the response
```

---

## Common Issues with AIMessage

### Issue 1: Incomplete Tool Calls
**Problem:** `AIMessage` with `tool_calls` but no `ToolMessage`

**Solution:** Clean up incomplete tool calls (what we just fixed!)

### Issue 2: Missing Content
**Problem:** `AIMessage` with only `tool_calls`, no `content`

**Solution:** Provide default content or handle gracefully

### Issue 3: Orphaned ToolMessages
**Problem:** `ToolMessage` without corresponding `AIMessage` with tool call

**Solution:** Usually OK, but can be cleaned up

---

## Summary

**AIMessage is:**
- ✅ A LangChain class representing AI assistant messages
- ✅ Part of the conversation history
- ✅ Can contain tool calls (requests to execute functions)
- ✅ Must be paired with ToolMessages when tool calls are present
- ✅ Converted to audio via TTS in this project

**Key Takeaway:**
Think of `AIMessage` as "what the AI said" - it can be:
- A simple text response: `AIMessage(content="Hello!")`
- A tool call request: `AIMessage(tool_calls=[...])`
- Both: `AIMessage(content="I'll do that.", tool_calls=[...])`

In your voice agent, `AIMessage` objects flow through:
```
LangGraph Agent → AIMessage → Adapter → LiveKit → TTS → Your Ears
```

