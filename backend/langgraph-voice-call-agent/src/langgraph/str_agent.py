"""
str_agent.py — Multi-Agent STR (Short-Term Rental) Supervisor for LangGraph Server.

Architecture:
  Supervisor (The Manager)
   ├─ Market Scout       → uses OpenBnB MCP server (Airbnb search) — lazy async init
   ├─ Portfolio Analyst  → uses direct SQLite tools (instant, no MCP)
   └─ Comms Assistant    → drafts Slack / email messages (no tools, instant)

Key design: Portfolio Analyst and Comms Assistant are created at module level
(no async needed). Only Market Scout requires lazy MCP initialization because
the Airbnb MCP server is an external npm package started via stdio transport.
"""

import asyncio
import json
import logging
import pathlib
import sqlite3
from typing import Any

from blockbuster.blockbuster import blockbuster_skip
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger("str_agent")

# ── Paths ─────────────────────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent
DB_PATH = ROOT / "my_rentals.db"

# ── Module-level globals for lazy MCP init (Market Scout only) ────────

_mcp_client: MultiServerMCPClient | None = None
_market_scout: Any = None
_init_lock: asyncio.Lock | None = None


def _get_supervisor_llm(temperature: float = 0.2):
    """Sonnet for the supervisor — strong reasoning for routing and natural voice synthesis."""
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=temperature,
        max_tokens=1024,
    )


def _get_subagent_llm(temperature: float = 0.2):
    """Haiku for sub-agents — cheap and fast for structured tool calling."""
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=temperature,
        max_tokens=4096,
    )


def _get_airbnb_mcp_config() -> dict:
    """Return the MCP server connection config for Airbnb only."""
    return {
        "airbnb": {
            "command": "npx",
            "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
            "transport": "stdio",
        },
    }


# ── Agent Prompts ─────────────────────────────────────────────────────

MARKET_SCOUT_PROMPT = """You are the Market Scout — a short-term rental market research specialist.

Your job is to search Airbnb for listings that match the criteria given to you
(location, price range, property type, guest count, dates, etc.) and return a
structured summary of what you find.

When reporting results, always include for each listing:
- Listing name / title
- Nightly price
- Rating and number of reviews
- Number of bedrooms / guests
- Key amenities or highlights

If the user mentions a price cap (e.g. "under $250/night"), use the price filter.
Always search in the city/area specified. Default to checking availability for
the upcoming weekend if no dates are given.

Be concise and data-focused. Return factual findings, not opinions."""


PORTFOLIO_ANALYST_PROMPT = """You are the Portfolio Analyst — an internal data specialist for a property management company.

You have access to the company's private portfolio database containing property
details, pricing, occupancy rates, revenue history, and owner information.

Your job is to:
1. Look up the specific property(ies) the user is asking about
2. Pull performance metrics (occupancy, revenue, pricing trends)
3. Compare internal data against any market data provided
4. Identify if properties are overpriced, underpriced, or well-positioned

When comparing to market data, calculate specific differences:
- Price difference ($ and %)
- Occupancy vs. market average
- Revenue implications of price changes

Always ground your analysis in the actual numbers from the database.
If you need to find a property, search by address or name first."""


COMMS_ASSISTANT_PROMPT = """You are the Communications Assistant — a professional message drafter for property management.

Based on the analysis and findings provided to you, draft clear, professional,
and actionable messages. These could be:
- Slack messages to property owners about pricing adjustments
- Email drafts to the operations team
- Summary reports for stakeholders

Guidelines:
- Be concise but include the key data points that justify the recommendation
- Use a professional yet friendly tone
- Include specific numbers (current price, suggested price, expected impact)
- End with a clear call-to-action
- Format appropriately for the target channel (Slack = shorter, Email = more formal)

Do NOT make up data. Only use information that has been provided to you."""


SUPERVISOR_PROMPT = """You are an AI-powered property management voice assistant and team coordinator.

You already know our full portfolio data (below). Answer property questions DIRECTLY
from this data — no need to delegate. Only use tools for tasks you cannot do yourself.

YOUR PORTFOLIO (5 active properties, all in Austin TX):

1. Maple Street Retreat — 123 Maple St. Entire home, 3BR/2BA, sleeps 8.
   Rate: $225/night, cleaning $85. Occupancy: 72%, rating: 4.81 (47 reviews).
   Dec revenue: $4,860. Owner: Sarah Chen (sarah.chen@email.com).
   Trend: Jul $5,100 → Aug $5,400 → Sep $4,200 → Oct $3,800 → Nov $4,500 → Dec $4,860.

2. Downtown Loft — 456 Congress Ave. Entire apartment, 1BR/1BA, sleeps 3.
   Rate: $165/night, cleaning $50. Occupancy: 85%, rating: 4.93 (112 reviews).
   Dec revenue: $4,208. Owner: Sarah Chen.
   Trend: Jul $4,100 → Aug $4,350 → Sep $3,900 → Oct $3,600 → Nov $4,000 → Dec $4,208.

3. Lakeside Bungalow — 789 Lake Austin Blvd. Entire home, 4BR/3BA, sleeps 10.
   Rate: $310/night, cleaning $120. Occupancy: 61%, rating: 4.67 (29 reviews).
   Dec revenue: $5,673. Owner: Marcus Webb (marcus.webb@email.com).
   Trend: Jul $6,200 → Aug $6,800 → Sep $5,100 → Oct $4,600 → Nov $5,200 → Dec $5,673.

4. South Congress Studio — 1010 S Congress Ave. Private room, 1BR/1BA, sleeps 2.
   Rate: $89/night, cleaning $30. Occupancy: 91%, rating: 4.88 (203 reviews).
   Dec revenue: $2,431. Owner: Sarah Chen.
   Trend: Jul $2,500 → Aug $2,600 → Sep $2,300 → Oct $2,100 → Nov $2,350 → Dec $2,431.

5. Hill Country Villa — 2200 Barton Creek Dr. Entire home, 5BR/4BA, sleeps 12.
   Rate: $475/night, cleaning $200. Occupancy: 52%, rating: 4.45 (15 reviews).
   Dec revenue: $7,410. Owner: Marcus Webb.
   Trend: Jul $8,200 → Aug $8,800 → Sep $6,500 → Oct $5,800 → Nov $6,900 → Dec $7,410.

PORTFOLIO TOTALS (Dec): $24,581 total revenue, avg occupancy 72%, avg rate $253, avg rating 4.75.
OWNERS: Sarah Chen (3 properties), Marcus Webb (2 properties).

YOUR SPECIALIST AGENTS (use only when needed):

1. **call_market_scout** — Searches Airbnb for competitor listings. ONLY use when the
   user explicitly asks to compare with the market or competitors. This is SLOW (~15s).

2. **call_comms_assistant** — Drafts professional messages (Slack, email, WhatsApp).
   Use when the user wants to send a message to owners, guests, or team.
   Include the relevant data in your request so they can write accurately.

WORKFLOW:
- Property questions → answer DIRECTLY from the data above. Do NOT use any tools.
- Market comparisons → call_market_scout
- Drafting messages → call_comms_assistant with relevant data context
- General conversation → respond directly

CRITICAL RULES — you are a VOICE assistant. Users hear your responses spoken aloud.
1. NEVER output JSON, raw data, code, or tool output. ALWAYS respond in plain conversational English.
2. Lead with the key takeaway, then one or two supporting numbers.
3. No markdown, no bullet lists, no headers, no brackets — just natural spoken language.
4. Keep responses concise — under 4 sentences when possible."""


# ── Lazy MCP initialization (Market Scout only) ─────────────────────

async def _ensure_market_scout_initialized():
    """Initialize Airbnb MCP client and Market Scout on first call.

    Only the Market Scout needs MCP (external Airbnb server via npx).
    Portfolio Analyst and Comms Assistant are created at module level.
    """
    global _mcp_client, _market_scout, _init_lock

    if _init_lock is None:
        _init_lock = asyncio.Lock()

    async with _init_lock:
        if _market_scout is not None:
            return  # Already initialized

        logger.info("Initializing Airbnb MCP client (first market_scout call)...")

        # Connect to Airbnb MCP server — skip blockbuster's blocking-call
        # detection because MCP stdio transport calls shutil.which / os.access.
        skip_token = blockbuster_skip.set(True)
        try:
            _mcp_client = MultiServerMCPClient(_get_airbnb_mcp_config())
            airbnb_tools = await _mcp_client.get_tools()
        finally:
            blockbuster_skip.reset(skip_token)

        logger.info(f"Loaded {len(airbnb_tools)} Airbnb tools")

        _market_scout = create_react_agent(
            _get_subagent_llm(), tools=airbnb_tools, prompt=MARKET_SCOUT_PROMPT
        )

        logger.info("Market Scout initialized successfully")


# ── Direct portfolio tools (no MCP, no sub-agent) ────────────────────

def _db_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read-only query against the portfolio database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@tool
def list_properties() -> str:
    """List all properties in the portfolio with key details: name, address, city, nightly rate, occupancy, rating, revenue, and owner."""
    rows = _db_query("""
        SELECT id, name, address, city, state, property_type,
               bedrooms, max_guests, nightly_rate, avg_occupancy,
               avg_rating, total_reviews, last_month_revenue, status, owner_name
        FROM properties ORDER BY id
    """)
    return json.dumps(rows, indent=2)


@tool
def search_property(query: str) -> str:
    """Search for a property by name or address (partial match). Use when the user refers to a property like 'Hill Country Villa' or 'Downtown Loft'."""
    rows = _db_query("""
        SELECT id, name, address, city, nightly_rate, avg_occupancy,
               avg_rating, last_month_revenue, owner_name, owner_email
        FROM properties
        WHERE name LIKE ? OR address LIKE ?
        ORDER BY id
    """, (f"%{query}%", f"%{query}%"))
    if not rows:
        return json.dumps({"message": f"No properties matching '{query}'"})
    return json.dumps(rows, indent=2)


@tool
def get_performance_history(property_id: int, months: int = 6) -> str:
    """Get monthly performance history for a property: revenue, occupancy, bookings, avg nightly rate, and expenses."""
    rows = _db_query("""
        SELECT p.name, mp.month, mp.revenue, mp.occupancy,
               mp.bookings, mp.avg_nightly, mp.expenses
        FROM monthly_performance mp
        JOIN properties p ON p.id = mp.property_id
        WHERE mp.property_id = ?
        ORDER BY mp.month DESC LIMIT ?
    """, (property_id, months))
    if not rows:
        return json.dumps({"error": f"No performance data for property {property_id}"})
    return json.dumps(rows, indent=2)


@tool
def get_portfolio_summary() -> str:
    """Get a high-level summary of the entire portfolio: total properties, average occupancy, total revenue, avg nightly rate, and per-property breakdown."""
    rows = _db_query("""
        SELECT COUNT(*) AS total_properties,
               ROUND(AVG(avg_occupancy), 2) AS avg_occupancy,
               ROUND(SUM(last_month_revenue), 2) AS total_last_month_revenue,
               ROUND(AVG(nightly_rate), 2) AS avg_nightly_rate,
               ROUND(AVG(avg_rating), 2) AS avg_rating
        FROM properties WHERE status = 'active'
    """)
    summary = rows[0] if rows else {}
    per_prop = _db_query("""
        SELECT name, nightly_rate, avg_occupancy, last_month_revenue, avg_rating
        FROM properties WHERE status = 'active'
        ORDER BY last_month_revenue DESC
    """)
    summary["properties"] = per_prop
    return json.dumps(summary, indent=2)


# ── Tool wrappers for the supervisor ─────────────────────────────────

async def _run_subagent(subagent: Any, request: str) -> str:
    """Invoke a sub-agent with blockbuster skip (MCP stdio uses os.read/write)."""
    skip_token = blockbuster_skip.set(True)
    try:
        result = await subagent.ainvoke(
            {"messages": [HumanMessage(content=request)]}
        )
    finally:
        blockbuster_skip.reset(skip_token)
    return result["messages"][-1].content


@tool
async def call_portfolio_analyst(request: str) -> str:
    """Query the internal portfolio database for property details, performance
    metrics, occupancy rates, revenue data, and owner information.
    Input: Natural language question about our properties or portfolio.
    """
    return await _run_subagent(_portfolio_analyst_agent, request)


@tool
async def call_market_scout(request: str) -> str:
    """[SLOW — ~15s, uses external API] Search Airbnb for competitor listings and market data.
    ONLY use this when the user EXPLICITLY asks to compare with the market, competitors,
    or Airbnb listings. Do NOT use for questions about our own properties.
    Input: Natural language market research request with location and criteria.
    """
    await _ensure_market_scout_initialized()
    return await _run_subagent(_market_scout, request)


@tool
async def call_comms_assistant(request: str) -> str:
    """Draft professional messages (Slack, email, WhatsApp) to property owners,
    guests, or team members. Always include relevant data and context in your
    request so the drafter can write accurately.
    Input: Who to message, what about, and any relevant data or findings.
    """
    return await _run_subagent(_comms_assistant_agent, request)


# ── Module-level sub-agents (no async needed — instant) ──────────────

_portfolio_analyst_agent = create_react_agent(
    _get_subagent_llm(),
    tools=[list_properties, search_property, get_performance_history, get_portfolio_summary],
    prompt=PORTFOLIO_ANALYST_PROMPT,
)

_comms_assistant_agent = create_react_agent(
    _get_subagent_llm(),
    tools=[],
    prompt=COMMS_ASSISTANT_PROMPT,
)

# ── Module-level compiled graph (loaded synchronously by LangGraph server) ──

agent = create_react_agent(
    _get_supervisor_llm(),
    tools=[
        call_market_scout, call_comms_assistant,
    ],
    prompt=SUPERVISOR_PROMPT,
)
