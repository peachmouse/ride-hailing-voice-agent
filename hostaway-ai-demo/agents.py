"""
agents.py — Multi-Agent LangGraph system with Supervisor pattern.

Architecture
============
Supervisor (The Manager)
 ├─ Market Scout       → uses OpenBnB MCP server (Airbnb search)
 ├─ Portfolio Analyst  → uses local SQLite MCP server (internal data)
 └─ Comms Assistant    → drafts Slack / email messages from findings

The supervisor receives the user query, decides which agents to call and
in what order, gathers their results, and synthesizes a final answer.
"""

import os
import asyncio
import pathlib
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# ── Paths ─────────────────────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent
PORTFOLIO_SERVER = str(ROOT / "portfolio_mcp_server.py")


# ── LLM ───────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.2):
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=temperature,
        max_tokens=4096,
    )


# ── MCP Client Configuration ─────────────────────────────────────────

def get_mcp_config() -> dict:
    """Return the MCP server connection config."""
    return {
        "airbnb": {
            "command": "npx",
            "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
            "transport": "stdio",
        },
        "portfolio": {
            "command": "python",
            "args": [PORTFOLIO_SERVER],
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


SUPERVISOR_PROMPT = """You are the Supervisor of an AI-powered property management intelligence system.
You coordinate three specialist agents to answer questions about short-term rental
properties and market conditions.

Your team:
1. **market_scout** — Searches Airbnb for competitor listings and market data.
   Call this when you need external market intelligence (competitor prices,
   availability, ratings, amenities).

2. **portfolio_analyst** — Queries the internal property database for your
   company's own listings, revenue, occupancy, and performance history.
   Call this when you need internal/private business data.

3. **comms_assistant** — Drafts professional messages (Slack, email) based on
   findings. Call this LAST, after you have gathered data from the other agents.

Workflow for a typical comparison query:
1. First call portfolio_analyst to get internal property data
2. Then call market_scout to get comparable market listings
3. Finally call comms_assistant if a message needs to be drafted

Always synthesize the findings from all agents into a clear, actionable answer.
Include specific numbers and comparisons. If the user asks for a message to be
drafted, make sure to include it in your final response."""


# ── Build the multi-agent graph ───────────────────────────────────────

async def build_graph():
    """
    Build and return the compiled LangGraph supervisor agent.

    This sets up:
    - MCP connections to both the Airbnb and Portfolio servers
    - Three specialized sub-agents, each with their own tools and prompts
    - A supervisor agent that orchestrates them via tool-calling
    """
    llm = get_llm()

    # Connect to MCP servers and load tools
    client = MultiServerMCPClient(get_mcp_config())

    all_tools = await client.get_tools()

    # Split tools by server
    airbnb_tools = [t for t in all_tools if t.name.startswith("airbnb")]
    portfolio_tools = [t for t in all_tools if not t.name.startswith("airbnb")]

    # ── Create specialized sub-agents ─────────────────────────────────

    market_scout = create_react_agent(
        llm,
        tools=airbnb_tools,
        prompt=MARKET_SCOUT_PROMPT,
    )

    portfolio_analyst = create_react_agent(
        llm,
        tools=portfolio_tools,
        prompt=PORTFOLIO_ANALYST_PROMPT,
    )

    # Comms assistant has no MCP tools — it just drafts messages
    comms_assistant = create_react_agent(
        llm,
        tools=[],
        prompt=COMMS_ASSISTANT_PROMPT,
    )

    # ── Wrap sub-agents as tools for the supervisor ───────────────────
    from langchain_core.tools import tool

    @tool
    async def market_scout_tool(request: str) -> str:
        """Search Airbnb for competitor listings and market data.
        Use this to find real-time market prices, ratings, and availability
        for short-term rentals in a specific area. Provide the location,
        price range, property type, and any other search criteria.
        Input: Natural language market research request.
        """
        result = await market_scout.ainvoke(
            {"messages": [HumanMessage(content=request)]}
        )
        # Return the final AI message
        return result["messages"][-1].content

    @tool
    async def portfolio_analyst_tool(request: str) -> str:
        """Query the internal property portfolio database.
        Use this to look up your company's own properties, revenue,
        occupancy rates, performance history, and owner information.
        You can search by property address, name, or ask for portfolio summaries.
        Input: Natural language query about internal property data.
        """
        result = await portfolio_analyst.ainvoke(
            {"messages": [HumanMessage(content=request)]}
        )
        return result["messages"][-1].content

    @tool
    async def comms_assistant_tool(request: str) -> str:
        """Draft a professional message (Slack, email, or report).
        Use this AFTER gathering data from the other agents.
        Provide all the relevant data and context, specify the channel
        (Slack/email) and recipient, and describe what the message should convey.
        Input: Context + data + drafting instructions.
        """
        result = await comms_assistant.ainvoke(
            {"messages": [HumanMessage(content=request)]}
        )
        return result["messages"][-1].content

    # ── Create the supervisor ─────────────────────────────────────────

    supervisor = create_react_agent(
        llm,
        tools=[market_scout_tool, portfolio_analyst_tool, comms_assistant_tool],
        prompt=SUPERVISOR_PROMPT,
    )

    return supervisor, client


# ── Convenience runner ────────────────────────────────────────────────

async def run_query(query: str):
    """Run a single query through the full multi-agent system."""
    supervisor, client = await build_graph()
    result = await supervisor.ainvoke(
        {"messages": [HumanMessage(content=query)]}
    )
    return result


# ── CLI entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "How does my listing at 123 Maple St compare to local rentals "
        "in Austin under $250/night? If I'm overpriced, draft a Slack "
        "message to the owner suggesting a 10% price drop."
    )

    print(f"\n{'='*70}")
    print(f"  Query: {query}")
    print(f"{'='*70}\n")

    result = asyncio.run(run_query(query))

    print(f"\n{'='*70}")
    print("  FINAL ANSWER")
    print(f"{'='*70}\n")
    print(result["messages"][-1].content)
