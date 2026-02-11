# 🏠 STR Market & Portfolio Intelligence Hub

> A multi-agent AI system for short-term rental property management, built with **LangGraph** (Supervisor pattern), **MCP** (Model Context Protocol), and **Claude**.

**Demo scenario:** A property manager asks: *"How does my listing at 123 Maple St compare to local rentals under $250/night? If I'm overpriced, draft a Slack message to my owner suggesting a 10% price drop."*

The system orchestrates three AI agents to research the market, analyze internal data, and draft the communication — all in one flow.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                     │
│              Chat interface + Agent activity log             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 SUPERVISOR AGENT (LangGraph)                 │
│          Receives query → routes → synthesizes answer        │
│                                                             │
│  Tools:  market_scout | portfolio_analyst | comms_assistant  │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌──────────────┐  ┌───────────────┐  ┌────────────────┐
│ Market Scout │  │   Portfolio   │  │     Comms      │
│    Agent     │  │   Analyst     │  │   Assistant    │
│              │  │    Agent      │  │    Agent       │
│  Airbnb MCP  │  │  SQLite MCP   │  │  (no tools)   │
│   Server     │  │   Server      │  │  Drafts msgs   │
│  (OpenBnB)   │  │  (local DB)   │  │               │
└──────┬───────┘  └──────┬────────┘  └────────────────┘
       │                 │
       ▼                 ▼
  ┌─────────┐     ┌──────────┐
  │ Airbnb  │     │  SQLite  │
  │ (live   │     │  (mock   │
  │ scrape) │     │ portfolio│
  │         │     │   data)  │
  └─────────┘     └──────────┘
   EXTERNAL         INTERNAL
```

### MCP Servers

| Server | Transport | Source | Purpose |
|--------|-----------|--------|---------|
| **OpenBnB Airbnb** | stdio (npx) | Community MCP server | Real-time Airbnb listing search — no API key needed |
| **Portfolio PMS** | stdio (Python) | `portfolio_mcp_server.py` | Internal property data, revenue, occupancy, owner info |

### Agent Roles

| Agent | MCP Tools | Responsibility |
|-------|-----------|----------------|
| **Market Scout** | `airbnb_search`, `airbnb_listing_details` | Search competitor listings, pricing, ratings |
| **Portfolio Analyst** | `list_portfolio_properties`, `search_property`, `get_performance_history`, `get_portfolio_summary`, `run_portfolio_query` | Query internal property database |
| **Comms Assistant** | *(none)* | Draft Slack/email messages from findings |
| **Supervisor** | *(wraps the 3 agents above as tools)* | Route queries, orchestrate workflow, synthesize answers |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the Airbnb MCP server via `npx`)
- **Anthropic API key** ([get one here](https://console.anthropic.com/))

### 1. Clone & Install

```bash
cd hostaway-ai-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Create the Portfolio Database

```bash
python setup_db.py
# ✅  Database created at ./my_rentals.db
#     → 5 properties with 6 months of performance history each
```

### 4. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### Alternative: CLI Mode

```bash
# Run a single query from the command line
python agents.py "Show me our portfolio summary"

# Or use the default demo query
python agents.py
```

---

## Example Queries to Demo

| Query | Agents Involved | What It Demonstrates |
|-------|-----------------|---------------------|
| "How does my listing at 123 Maple St compare to local rentals in Austin under $250/night?" | Scout + Analyst | Cross-data-source comparison |
| "If I'm overpriced, draft a Slack message to the owner suggesting a 10% drop." | Scout + Analyst + Comms | Full 3-agent pipeline |
| "Show me our entire portfolio performance." | Analyst only | Internal data retrieval |
| "Search for 2-bedroom listings in Austin under $200/night." | Scout only | Live Airbnb market search |
| "What's our best property? Compare it to Airbnb competition." | Analyst + Scout | Analytical reasoning across sources |
| "Draft an email to Marcus Webb about the Villa's low occupancy." | Analyst + Comms | Data-informed communication |

---

## Project Structure

```
hostaway-ai-demo/
├── app.py                    # Streamlit UI
├── agents.py                 # LangGraph multi-agent system
├── portfolio_mcp_server.py   # Local SQLite MCP server
├── setup_db.py               # Database creation script
├── my_rentals.db             # SQLite database (generated)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
└── README.md                 # This file
```

---

## Interview Talking Points

When presenting this demo, highlight these key points:

### 1. MCP Standardization
> "Because I used MCP, I could swap the local SQLite server for a real Hostaway API server without changing a single line of the LangGraph orchestration code. The protocol abstracts the data source."

### 2. Supervisor Pattern Benefits
> "The supervisor pattern gives us centralized control over the workflow. It decides what data to gather and in what order — for example, it knows to pull internal data BEFORE searching Airbnb, so the market search can be more targeted."

### 3. Cross-Protocol Data Fusion
> "The system 'thinks' across two fundamentally different data protocols — live scraped public data vs. private SQL data — and synthesizes them into a single actionable insight."

### 4. Human-in-the-Loop Ready
> "In production, I'd add a LangGraph breakpoint before the communication step, so the property manager reviews and approves the message before it's sent. The architecture supports this natively."

### 5. Cost-Aware Model Selection
> "In a production deployment, I'd use Claude Haiku for the routing/classification step (the supervisor's initial analysis) and Claude Sonnet only for the complex synthesis — cutting costs by 80% on the routing layer."

### 6. Handling Real Constraints
> "I built this without access to the Hostaway or Airbnb APIs. This demonstrates a key PM skill: delivering a working prototype under data access constraints by finding creative alternatives."

---

## Extending This Demo

Ideas for making this even more impressive:

- **Add a 4th agent** for pricing optimization using historical trends
- **Integrate LangSmith** for observability — show trace visualizations
- **Add memory** with LangGraph's `InMemorySaver` for multi-turn conversations
- **Deploy to LangGraph Cloud** for a production-ready hosted version
- **Add real Slack integration** via Slack MCP server for live message sending

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Claude Sonnet 4.5 (Anthropic) |
| Agent Framework | LangGraph (Supervisor pattern) |
| Tool Protocol | Model Context Protocol (MCP) |
| External Data | OpenBnB MCP Server (Airbnb) |
| Internal Data | SQLite + custom MCP server |
| UI | Streamlit |
| Language | Python 3.11+ |
