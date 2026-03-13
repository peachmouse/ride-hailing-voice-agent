# Voice AI Stack Overview

Our demo uses a four-layer voice pipeline:

| Layer | Component | Role |
|-------|-----------|------|
| **Transport** | LiveKit | Real-time audio streaming between user and agent |
| **STT** | Deepgram Nova-3 | Speech-to-text with keyword boosting for domain terms (pickup, dropoff, booking IDs) |
| **Reasoning** | Claude Sonnet 4.5 via LangGraph | AI agent that handles slot extraction, disambiguation, and booking logic |
| **TTS** | Cartesia Sonic-2 | Text-to-speech with sub-100ms latency for natural conversation flow |

## Why these choices

- **Deepgram Nova-3** offers the lowest latency and highest accuracy for real-time streaming STT, with keyword boosting to improve recognition of FreeNow-specific terms — critical for correctly capturing location names and booking IDs over the phone.

- **Cartesia Sonic-2** delivers the fastest time-to-first-audio of any production TTS, eliminating awkward pauses between the user's question and the agent's response.

- **Claude Sonnet 4.5** provides the reasoning capability that makes this more than an IVR — it extracts multiple booking details from a single utterance, disambiguates locations, and handles mid-conversation changes naturally.

- **LiveKit** serves as the WebRTC transport for this browser-based demo. **In production at FreeNow, this layer would be replaced by Aircall**, which provides the same real-time audio transport over your existing telephony infrastructure. The STT, reasoning, and TTS layers remain unchanged — only the transport layer swaps out.

The architecture is deliberately modular: each layer can be replaced independently without affecting the others.
