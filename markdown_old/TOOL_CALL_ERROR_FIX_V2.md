# 🔧 Tool Call Error Fix - Version 2

## The Problem

**Error:** `ValueError: Found AIMessages with tool_calls that do not have a corresponding ToolMessage`

### Root Cause

The issue occurs because:

1. **ChatContext doesn't include ToolMessages** - LiveKit's ChatContext only tracks user and assistant messages, not tool execution results
2. **Incomplete state** - When we build state from ChatContext, we get AIMessages with `tool_calls` but no corresponding ToolMessages
3. **LangGraph validation fails** - LangGraph requires every tool call to have a ToolMessage response

### Why This Happens

```
Previous conversation:
  User: "Delete todo 2"
  Agent: [AIMessage with tool_calls=[delete_todo(2)]]
  Tool: [ToolMessage with result]
  Agent: "Deleted todo 2"

Current conversation (from ChatContext):
  User: "List my todos"
  Agent: [AIMessage with tool_calls=[delete_todo(2)]]  ← Incomplete!
  (Missing ToolMessage)
```

When we rebuild state from ChatContext, we only get user/assistant messages, not tool execution details.

## The Fix

**Solution:** Filter out AIMessages with tool_calls when building state from ChatContext.

### Why This Works

1. **LangGraph manages complete state internally** - It uses `thread_id` to fetch the complete conversation history, including ToolMessages
2. **ChatContext is for display only** - It's meant for showing conversation to users, not for maintaining complete agent state
3. **Tool calls are handled by LangGraph** - When LangGraph processes a new message, it has access to the complete state (including ToolMessages) via the thread_id

### Implementation

```python
# Filter out AIMessages with tool_calls
filtered_messages = []
for msg in messages:
    if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
        # Skip - LangGraph will handle these internally
        continue
    filtered_messages.append(msg)
```

### How It Works Now

```
1. User speaks: "List my todos"
   ↓
2. ChatContext built: [HumanMessage("List my todos")]
   ↓
3. State filtered: Removes any AIMessages with tool_calls
   ↓
4. Passed to LangGraph: Only clean messages
   ↓
5. LangGraph fetches complete state internally (using thread_id)
   - Includes all ToolMessages from previous interactions
   ↓
6. LangGraph processes: Calls list_todos tool
   ↓
7. Returns response: "Here are your todos..."
```

## Key Insight

**ChatContext ≠ Complete State**

- **ChatContext**: User-facing conversation history (what users see)
- **LangGraph State**: Complete agent state (includes tool calls, ToolMessages, internal state)

We should use ChatContext for display, but let LangGraph manage the complete state internally.

## Testing

After this fix:
1. ✅ Tool calls work correctly
2. ✅ No more "incomplete tool calls" errors
3. ✅ Conversation state is maintained properly
4. ✅ Previous tool calls are accessible via LangGraph's internal state

## Status

✅ **Fixed** - AIMessages with tool_calls are filtered out when building state from ChatContext. LangGraph handles tool calls using its internal state management.

