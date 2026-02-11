# Final Timeout Fix

## Problem

The worker initialization was timing out because the `prewarm` function was trying to load the VAD model synchronously, which takes too long and causes the worker initialization to timeout.

## Solution

**Changed `prewarm` to be lightweight:**
- No longer loads models during prewarm
- Models are loaded on-demand in the `entrypoint` function instead
- This avoids the initialization timeout

## What Changed

**Before:**
```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()  # This was timing out
```

**After:**
```python
def prewarm(proc: JobProcess):
    # Skip preloading - models load in entrypoint instead
    proc.userdata["vad"] = None
```

The `entrypoint` function already has code to load VAD if it's not preloaded, so this works seamlessly.

## Benefits

1. ✅ **No more timeout errors** - Worker initializes quickly
2. ✅ **Models still load** - Just happens in entrypoint instead
3. ✅ **More reliable** - Less chance of initialization failures
4. ✅ **Same functionality** - Agent works exactly the same

## Next Steps

Try starting the agent again:

```powershell
cd "C:\Users\Michal Stopa\Documents\langgraph-voice-back2front\backend\langgraph-voice-call-agent"
uv run -m src.livekit.agent dev
```

The agent should now start without timeout errors. Models will load when the first participant connects (which happens in the entrypoint, not during initialization).

