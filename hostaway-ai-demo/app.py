"""
app.py — Streamlit UI for the STR Market & Portfolio Intelligence Hub.

Run:  streamlit run app.py
"""

import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# ── Page config ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="STR Intelligence Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────

st.markdown("""
<style>
    .agent-card {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid;
    }
    .agent-scout { background: #EBF5FB; border-color: #2E86C1; }
    .agent-analyst { background: #F5EEF8; border-color: #8E44AD; }
    .agent-comms { background: #EAFAF1; border-color: #27AE60; }
    .agent-supervisor { background: #FEF9E7; border-color: #F39C12; }
    .agent-label {
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }
    .stChatMessage { max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/building.png", width=60)
    st.title("STR Intelligence Hub")
    st.caption("Multi-Agent AI for Short-Term Rental Management")

    st.divider()

    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    **Supervisor** (LangGraph)
    - 🔍 **Market Scout** → Airbnb MCP
    - 📊 **Portfolio Analyst** → SQLite MCP
    - 💬 **Comms Assistant** → Message Drafting
    """)

    st.divider()

    st.markdown("### 💡 Try these queries")
    examples = [
        "How does my listing at 123 Maple St compare to local rentals in Austin under $250/night? If I'm overpriced, draft a Slack message to the owner suggesting a 10% price drop.",
        "Show me a summary of our entire portfolio performance.",
        "Search for 2-bedroom Airbnb listings in Austin, TX under $200/night.",
        "What's our best performing property? Compare its pricing to similar listings on Airbnb.",
        "Draft an email to Marcus Webb about the Hill Country Villa's low occupancy and suggest strategies.",
    ]
    for ex in examples:
        if st.button(ex[:65] + "...", key=ex[:20], use_container_width=True):
            st.session_state["pending_query"] = ex

    st.divider()
    st.markdown("### ⚙️ Configuration")
    show_agent_steps = st.toggle("Show agent activity", value=True)

    st.divider()
    st.caption("Built with LangGraph · MCP · Claude · Streamlit")


# ── Session state ─────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_steps" not in st.session_state:
    st.session_state.agent_steps = []


# ── Helper: Identify which agent produced a tool call ─────────────────

def classify_agent(tool_name: str) -> tuple[str, str, str]:
    """Return (agent_label, emoji, css_class) for a tool name."""
    if "market_scout" in tool_name:
        return "Market Scout", "🔍", "agent-scout"
    elif "portfolio_analyst" in tool_name:
        return "Portfolio Analyst", "📊", "agent-analyst"
    elif "comms_assistant" in tool_name:
        return "Comms Assistant", "💬", "agent-comms"
    else:
        return "Supervisor", "🎯", "agent-supervisor"


# ── Helper: Run query with streaming steps ────────────────────────────

async def run_with_steps(query: str):
    """Run the multi-agent system and collect intermediate steps."""
    from agents import build_graph

    supervisor, client = await build_graph()
    steps = []

    # Use stream to capture intermediate steps
    async for event in supervisor.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
    ):
        for node_name, node_output in event.items():
            messages = node_output.get("messages", [])
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        steps.append({
                            "type": "tool_call",
                            "agent": tc["name"],
                            "input": tc["args"].get("request", str(tc["args"])),
                        })
                elif isinstance(msg, ToolMessage):
                    content = msg.content
                    if len(content) > 500:
                        content = content[:500] + "..."
                    steps.append({
                        "type": "tool_result",
                        "agent": msg.name if hasattr(msg, "name") else "tool",
                        "output": content,
                    })

    # Get the final result
    result = await supervisor.ainvoke(
        {"messages": [HumanMessage(content=query)]}
    )
    final_answer = result["messages"][-1].content

    return final_answer, steps


def run_query_sync(query: str):
    """Synchronous wrapper for the async agent pipeline."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_with_steps(query))
    finally:
        loop.close()


# ── Main chat interface ───────────────────────────────────────────────

st.markdown("## 🏠 STR Market & Portfolio Intelligence Hub")
st.markdown(
    "Ask questions about your property portfolio, compare against Airbnb "
    "market data, and draft communications — all powered by a multi-agent "
    "AI system."
)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show agent steps if they exist for this message
        if msg["role"] == "assistant" and "steps" in msg and show_agent_steps:
            with st.expander("🔄 Agent Activity Log", expanded=False):
                for step in msg["steps"]:
                    label, emoji, css = classify_agent(step["agent"])
                    if step["type"] == "tool_call":
                        st.markdown(
                            f'<div class="agent-card {css}">'
                            f'<div class="agent-label">{emoji} {label} — Called</div>'
                            f'<code>{step["input"][:300]}</code></div>',
                            unsafe_allow_html=True,
                        )
                    elif step["type"] == "tool_result":
                        st.markdown(
                            f'<div class="agent-card {css}">'
                            f'<div class="agent-label">{emoji} {label} — Responded</div>'
                            f'{step["output"][:300]}</div>',
                            unsafe_allow_html=True,
                        )

# Handle pending query from sidebar buttons
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")
    st.session_state.messages.append({"role": "user", "content": query})
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about your properties or the market..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Process the last user message if it hasn't been answered
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
):
    query = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agents are working on your query..."):
            status = st.status("Multi-Agent Pipeline", expanded=True)
            status.write("🎯 **Supervisor** analyzing your request...")

            try:
                final_answer, steps = run_query_sync(query)

                # Update status with steps
                for step in steps:
                    label, emoji, _ = classify_agent(step["agent"])
                    if step["type"] == "tool_call":
                        status.write(f"{emoji} **{label}** searching...")
                    elif step["type"] == "tool_result":
                        status.write(f"✅ **{label}** returned results")

                status.update(label="Multi-Agent Pipeline — Complete ✅", state="complete")

                st.markdown(final_answer)

                # Save to history with steps
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "steps": steps,
                })

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.markdown(
                    "**Troubleshooting:**\n"
                    "- Is `ANTHROPIC_API_KEY` set in your `.env` file?\n"
                    "- Is Node.js 18+ installed? (needed for the Airbnb MCP server)\n"
                    "- Did you run `python setup_db.py` to create the database?\n"
                    "- Check the terminal for detailed error logs."
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "steps": [],
                })
