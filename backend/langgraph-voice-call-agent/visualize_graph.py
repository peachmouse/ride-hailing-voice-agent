"""Visualize the STR Supervisor LangGraph workflow as a PNG."""

from src.langgraph.str_agent import agent

png_bytes = agent.get_graph().draw_mermaid_png()

out_path = "str_supervisor_graph.png"
with open(out_path, "wb") as f:
    f.write(png_bytes)

print(f"Saved graph visualization to {out_path}")
