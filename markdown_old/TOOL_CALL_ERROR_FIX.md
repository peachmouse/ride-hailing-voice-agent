# 🔧 Tool Call Error Fix

## The Problem

**Error:** `ValueError: Found AIMessages with tool_calls that do not have a corresponding ToolMessage`

### What Happened

1. **Agent called `delete_todo` tool** - This created an `AIMessage` with `tool_calls`
2. **Tool used `interrupt()`** - The tool paused execution to ask for user confirmation
3. **Conversation state was rebuilt incorrectly** - When resuming, the adapter rebuilt state from LiveKit's `ChatContext`
4. **Missing ToolMessages** - The rebuilt state had the `AIMessage` with `tool_calls` but no corresponding `ToolMessage`
5. **LangGraph validation failed** - LangGraph requires every tool call to have a ToolMessage response

### Root Cause

The `LangGraphAdapter._run()` method was rebuilding conversation state from LiveKit's `ChatContext` instead of using LangGraph's actual state. This meant:

- ✅ LangGraph maintains complete state (including ToolMessages)
- ❌ Adapter was ignoring LangGraph's state and rebuilding from ChatContext
- ❌ ChatContext doesn't include ToolMessages (only user/assistant messages)
- ❌ Result: Incomplete conversation history

## The Fix

**Changed:** `_run()` now gets state from LangGraph first, then falls back to ChatContext only if no state exists.

### Before:
```python
state = self._chat_ctx_to_state()  # Rebuilds from ChatContext (incomplete)
```

### After:
```python
# Get state from LangGraph (complete, includes ToolMessages)
current_state = await self._graph.aget_state(config=self._llm._config)
if current_state and current_state.values and "messages" in current_state.values:
    state = {"messages": current_state.values["messages"]}  # Use LangGraph's state
else:
    state = self._chat_ctx_to_state()  # Fallback only if no state exists
```

## Why This Works

1. **LangGraph maintains complete state** - It tracks all messages including ToolMessages
2. **Tool calls are properly paired** - When a tool executes, LangGraph adds the ToolMessage
3. **State is preserved across interrupts** - LangGraph's state persists even when tools use `interrupt()`
4. **Adapter now uses complete state** - No more missing ToolMessages

## Testing

After this fix, the `delete_todo` tool should work correctly:

1. User: "Delete todo 2"
2. Agent: Calls `delete_todo(2)`
3. Tool: Uses `interrupt()` to ask "Are you sure?"
4. User: "Yes"
5. Tool: Returns "Deleted todo #2"
6. ✅ **No more errors** - ToolMessage is properly included in state

## Additional Changes

- Added `ToolMessage` import (for future use if needed)
- Added error handling for state retrieval
- Added logging for debugging

## Status

✅ **Fixed** - The adapter now uses LangGraph's complete state instead of rebuilding from ChatContext.

