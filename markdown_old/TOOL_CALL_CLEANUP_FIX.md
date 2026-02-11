# 🔧 Tool Call Cleanup Fix

## The Problem

**Error:** `ValueError: Found AIMessages with tool_calls that do not have a corresponding ToolMessage`

### Root Cause

When a tool call is interrupted (e.g., `delete_todo` uses `interrupt()` and the conversation ends before completion), LangGraph's internal state retains:
- An `AIMessage` with `tool_calls` (the agent wanted to call a tool)
- But no corresponding `ToolMessage` (the tool never completed)

When the next conversation starts, LangGraph validates the state and finds this incomplete tool call, causing the error.

### Why This Happens

1. **User asks to delete a todo** → Agent creates `AIMessage` with `tool_calls=[delete_todo]`
2. **Tool uses `interrupt()`** → Asks "Are you sure?"
3. **Conversation ends** → User disconnects or conversation times out
4. **State persists** → LangGraph saves state with incomplete tool call
5. **Next conversation** → LangGraph loads state, finds incomplete tool call, errors

## The Solution

**Clean up incomplete tool calls** from LangGraph's state before processing.

### Implementation

1. **Get state from LangGraph** (complete state with ToolMessages)
2. **Clean incomplete tool calls**:
   - For each `AIMessage` with `tool_calls`
   - Check if all tool calls have corresponding `ToolMessages`
   - If not, convert to regular `AIMessage` without `tool_calls`
3. **Use cleaned state** for processing

### Code Changes

```python
async def _run(self):
    # Get state from LangGraph
    current_state = await self._graph.aget_state(config=self._llm._config)
    if current_state and current_state.values and "messages" in current_state.values:
        messages = current_state.values["messages"]
        # Clean incomplete tool calls
        cleaned_messages = self._clean_incomplete_tool_calls(messages)
        state = {"messages": cleaned_messages}
    else:
        # No state exists yet
        state = self._chat_ctx_to_state()

@staticmethod
def _clean_incomplete_tool_calls(messages: list) -> list:
    """Remove AIMessages with tool_calls that don't have corresponding ToolMessages."""
    cleaned = []
    
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Check if all tool calls have ToolMessages
            tool_call_ids = [tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None) 
                           for tc in msg.tool_calls]
            
            has_all_tool_messages = all(
                any(isinstance(future_msg, ToolMessage) and 
                    getattr(future_msg, 'tool_call_id', None) == tc_id
                    for future_msg in messages[i + 1:])
                for tc_id in tool_call_ids
            )
            
            if has_all_tool_messages:
                cleaned.append(msg)  # Keep it
            else:
                # Convert to regular AIMessage without tool_calls
                cleaned.append(AIMessage(
                    content=msg.content or "Previous tool call was interrupted",
                    id=getattr(msg, 'id', None)
                ))
        else:
            cleaned.append(msg)  # Keep other messages
    
    return cleaned
```

## How It Works

### Before (Broken State):
```
Messages:
1. HumanMessage: "Delete todo 2"
2. AIMessage: tool_calls=[delete_todo(2)]  ← Incomplete! No ToolMessage
3. (Conversation ended)
```

### After (Cleaned State):
```
Messages:
1. HumanMessage: "Delete todo 2"
2. AIMessage: content="Previous tool call was interrupted"  ← Fixed!
```

## Benefits

1. **Prevents errors** - No more incomplete tool call errors
2. **Preserves context** - Keeps conversation history intact
3. **Graceful handling** - Converts incomplete calls to regular messages
4. **Automatic cleanup** - Happens transparently on each request

## Testing

After this fix:
1. Start a conversation
2. Ask to delete a todo (triggers `interrupt()`)
3. Disconnect before confirming
4. Start a new conversation
5. ✅ **No errors** - State is cleaned automatically

## Status

✅ **Fixed** - Incomplete tool calls are now automatically cleaned from state before processing.

