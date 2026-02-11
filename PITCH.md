# STR Voice AI Agent — Hostaway Pitch

## Tiered Model Architecture: A Well-Established Multi-Agent Pattern

This system uses a **supervisor + specialist** architecture where model selection is deliberately tiered by task complexity.

**The supervisor needs judgment, the sub-agents need execution.**

The supervisor's job is harder — it must understand the user's intent, decide which agents to call and in what order, and synthesize a coherent final answer. That's reasoning-heavy work where a more capable model pays for itself.

The sub-agents do narrow, well-defined tasks: run a SQL query, search Airbnb with specific filters, draft a message from provided data. They have explicit instructions, structured tool interfaces, and limited scope. A smaller model handles this reliably because the task is constrained.

| Layer | Model | Role | Why this model |
|-------|-------|------|----------------|
| Supervisor | Claude Sonnet 4.5 | Intent understanding, routing, synthesis | Needs strong reasoning to coordinate agents and produce natural spoken answers |
| Market Scout | Claude Haiku 4.5 | Airbnb search via MCP | Structured tool calling — constrained task |
| Portfolio Analyst | Claude Haiku 4.5 | SQL queries on portfolio DB | Structured tool calling — constrained task |
| Comms Assistant | Claude Haiku 4.5 | Draft messages | Template-like output from provided data |

**The cost math reinforces this.** In a typical request:
- The supervisor makes 2-3 LLM calls (route, maybe re-route, synthesize)
- Each sub-agent makes 2-4 calls (ReAct loop: reason, tool call, observe, respond)

Sub-agent calls are the majority of the token spend. Putting the cheaper model where the volume is gives the biggest savings without sacrificing quality where it matters.

**This generalizes broadly.** The pattern appears as:
- **"Router + specialist" architectures** — strong model routes, cheap models execute
- **"Tiered inference"** — use the most capable model only where the task demands it
- **Anthropic's own guidance** — Haiku for high-volume structured tasks, Sonnet/Opus for complex reasoning

The tradeoff to watch: if a sub-agent's task gets complex enough that Haiku starts making mistakes (wrong tool calls, poor reasoning chains), you bump just that agent to Sonnet. The architecture makes this a config change, not a redesign.

---

## System Architecture

```
Browser (Next.js :3000)
    ↕ WebSocket (LiveKit Client SDK)
LiveKit Server (Cloud or Docker :7880)
    ↕ WebSocket (LiveKit Agents SDK)
Python LiveKit Agent
    ↓ HTTP (RemoteGraph)
LangGraph Server (:2024)
    ↓ API calls
Claude API (LLM) + MCP Servers (tools)
```

### Audio Pipeline

```
User speaks → Silero VAD → Deepgram STT (nova-3) → LangGraph Agent → Cartesia TTS (sonic-2) → User hears
                                  ↑                                              |
                          Domain keyterms                                  Token streaming
                      (property, occupancy, etc.)                      (low-latency playback)
```

**STT tuning:** Deepgram nova-3 with domain-specific keyterm prompting ensures property names, financial terms, and industry jargon are transcribed accurately. Smart formatting handles numbers, currencies, and addresses.

**TTS quality:** Cartesia sonic-2 produces natural, conversational speech at low latency — critical for a voice agent that needs to feel like a real conversation, not a bot reading text.

### Agent Graph

```
User query
    ↓
Supervisor (Sonnet 4.5) — has portfolio data in context for instant answers
    ├─ call_market_scout    → Market Scout Agent (Haiku 4.5) → Airbnb MCP Server
    ├─ call_portfolio_analyst → Portfolio Analyst (Haiku 4.5) → SQLite tools (direct DB access)
    └─ call_comms_assistant → Comms Assistant (Haiku 4.5)    → (no tools, drafts from context)
    ↓
Supervisor synthesizes final answer in natural spoken language
```

**Optimization pattern:** The supervisor carries key portfolio metrics in its context window, allowing instant answers to common questions (occupancy, revenue, ratings) without any tool call. Sub-agents are reserved for complex queries requiring multi-step analysis, live market data, or specialized output like professional message drafting.

---

## Economics

### Per-Query Cost Breakdown

**Before optimization (all Sonnet 4.5):**
- Measured via LangSmith: ~44,000 tokens / $0.16 per query
- Extrapolated: 1,000 queries/day = ~$160/day = ~$4,800/month

**After optimization (Sonnet supervisor + Haiku sub-agents):**
- Estimated: ~44,000 tokens / ~$0.03-0.05 per query
- Extrapolated: 1,000 queries/day = ~$30-50/day = ~$900-1,500/month
- **~70% cost reduction** from model tiering alone

**Further optimization (context-loaded supervisor):**
- Common queries answered in 1 LLM call (~1,500 tokens) instead of 3-4 calls (~12,000 tokens)
- Estimated: ~$0.005-0.01 per direct-answer query
- Blended average (mix of direct + delegated): ~$0.02-0.04 per query

### Model Pricing Reference (Anthropic, as of 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|----------------------|
| Claude Sonnet 4.5 | $3.00 | $15.00 |
| Claude Haiku 4.5 | $0.80 | $4.00 |

### Where Tokens Go (Typical Query)

| Step | Calls | Token share | Cost share (all-Sonnet) |
|------|-------|-------------|------------------------|
| Supervisor reasoning | 2-3 | ~25% | ~25% |
| Sub-agent ReAct loops | 4-8 | ~65% | ~65% |
| Tool schemas + prompts | — | ~10% | ~10% |

Moving the 65% sub-agent share from Sonnet to Haiku pricing is what drives the savings.

### Additional Infrastructure Costs

| Service | Cost | Notes |
|---------|------|-------|
| LiveKit Cloud | Usage-based | ~$0.004/participant-minute |
| Deepgram STT (nova-3) | $0.0043/min | Pay-as-you-go, keyterm prompting included |
| Cartesia TTS (sonic-2) | Usage-based | Low-latency streaming synthesis |
| LangGraph Server | Self-hosted | No per-query cost |
| LangSmith (observability) | Free tier available | Paid plans for volume |

### Cost at Scale Estimate

| Scale | Queries/day | LLM cost/month | Voice infra/month | Total/month |
|-------|------------|----------------|-------------------|-------------|
| Pilot (1 PM) | 50 | $30-60 | ~$20 | ~$50-80 |
| Team (5 PMs) | 250 | $150-300 | ~$100 | ~$250-400 |
| Department (20 PMs) | 1,000 | $600-1,200 | ~$400 | ~$1,000-1,600 |

---

## Technical Key Decisions

### Why LangGraph (not raw LLM calls)?

- **Stateful conversations** — Thread IDs + checkpointing maintain context across reconnects
- **Hot-reloadable agents** — Change the agent graph without restarting the voice pipeline
- **RemoteGraph decoupling** — Agent runs as an HTTP service, not embedded in the voice process
- **Built-in streaming** — Token-level streaming for low-latency voice output
- **Multi-agent orchestration** — Supervisor pattern with tool-based delegation is a first-class primitive

### Why LiveKit (not direct WebRTC)?

- **Production-grade WebRTC** — Handles NAT traversal, TURN servers, codec negotiation
- **Agents SDK** — First-class support for AI voice agents with VAD, STT, TTS integration
- **Room abstraction** — Multiple participants, video tracks, screen sharing out of the box
- **Cloud + self-hosted** — Start with cloud, move to self-hosted if needed

### Why MCP for Tools?

- **Standardized protocol** — Tools are language-agnostic servers, not library functions
- **Isolation** — Each MCP server runs as a subprocess; crashes don't take down the agent
- **Ecosystem** — Growing library of pre-built MCP servers (Airbnb, databases, APIs)
- **Composability** — Add new data sources by adding an MCP server, not rewriting agent code
- **Hostaway integration path** — Hostaway's API could be wrapped as an MCP server, giving every agent instant access to reservations, listings, messaging, and analytics

### Context-Loaded Supervisor Pattern

The supervisor carries a snapshot of key portfolio metrics directly in its system prompt. This enables:
- **Instant answers** for the most common queries (occupancy, revenue, ratings, property details)
- **Zero tool-call latency** — no sub-agent delegation needed for routine lookups
- **Sub-agent delegation** reserved for complex tasks: live market data, multi-step analysis, message drafting
- **Data freshness** — the context snapshot is refreshed on each server restart; in production, this would be a scheduled cache update

This is a practical optimization for voice UX where response latency directly impacts user experience. A 3-second answer feels conversational; a 15-second answer feels broken.

### Lazy MCP Initialization

The Airbnb MCP server is an external npm package started via stdio transport. Rather than blocking server startup, the Market Scout's MCP connection initializes lazily on first invocation. Portfolio tools use direct database access, eliminating MCP overhead entirely for internal data queries.

---

## Hostaway-Specific Value Proposition

### The Problem
Property managers juggle multiple data sources daily — internal portfolios, market comparables, owner communications. This context-switching is slow and error-prone. Existing dashboards require clicking through multiple screens to answer questions that should be instant.

### The Solution
A voice-first AI agent that property managers can talk to naturally:
- "Give me a portfolio summary" → Instant overview of all properties, occupancy, and revenue
- "Which property has the best reviews?" → Data-driven answer with specific numbers
- "How do our prices compare to the market?" → Cross-references internal data with live Airbnb listings
- "Draft a Slack message to the owner about adjusting pricing" → Professional communication grounded in real data

### Why Voice?
- **Hands-free** — PMs are often on-site, driving between properties, or multitasking
- **Lower friction** — Speaking is faster than typing queries and navigating dashboards
- **Natural follow-ups** — Conversational flow enables iterative analysis without re-explaining context
- **Immediate insight** — Ask a question, get an answer in seconds, not minutes of dashboard navigation

### Integration Points with Hostaway
- **Portfolio data** → Connects to Hostaway's property/reservation database (currently SQLite demo; production would be Hostaway API via MCP)
- **Market intelligence** → Already searches Airbnb; could add VRBO, Booking.com MCPs for cross-platform comparison
- **Owner communications** → Could integrate with Hostaway's messaging system for direct owner outreach with AI-drafted messages
- **Revenue management** → Combine portfolio analytics with market data to surface pricing recommendations automatically
- **Operations** → Surface maintenance requests, cleaning schedules, guest check-in issues via voice

### Why This Matters for Hostaway's Strategy
- **MCP is the integration layer** — Hostaway's entire API surface could be exposed as MCP servers, making every data source instantly available to AI agents
- **Voice is the UX differentiator** — Most PMS tools are dashboard-first; a voice-first AI agent is a category-defining feature
- **Multi-agent scales** — New capabilities (revenue optimization, guest communication, maintenance scheduling) are added as new sub-agents, not rewrites
- **Cost-efficient at scale** — Tiered model architecture keeps per-query costs low enough for always-on, high-frequency use

---

## Demo Script

1. **Open the app** → Show dual-mode UI (voice + chat)
2. **Voice: "Give me a portfolio summary"** → Instant answer (~3-4s) from context-loaded supervisor. Shows natural spoken response with key metrics.
3. **Voice: "Which property has the highest revenue?"** → Direct answer from embedded data. Demonstrates the agent knows the portfolio deeply.
4. **Voice: "Tell me about the Downtown Loft"** → Property-specific deep dive with occupancy, revenue, ratings, and trends.
5. **Voice: "Draft a Slack message to Marcus Webb about improving the Hill Country Villa's occupancy"** → Triggers Comms Assistant sub-agent. Shows multi-agent delegation in action — supervisor passes data context, specialist drafts professional message.
6. **Voice: "Compare our pricing with similar Airbnb listings in Austin"** → Triggers Market Scout sub-agent via Airbnb MCP. Shows live external data integration. (Note: first call may take ~15s due to MCP initialization.)
7. **Show LangSmith** → Trace the multi-agent orchestration, token usage, and latency breakdown.
8. **Explain the architecture** → Tiered models, MCP tools, context-loading optimization, and how it maps to Hostaway's product.
