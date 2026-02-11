# 📊 Visualizing Your LangGraph

There are several ways to visualize your LangGraph agent. Here are the best options:

## Method 1: Using the Visualization Script (Easiest)

I've created a script that will generate a Mermaid diagram of your graph.

**Run it:**
```bash
cd backend/langgraph-voice-call-agent
uv run python visualize_graph.py
```

**What it does:**
- Lists all nodes in the graph
- Shows graph edges
- Generates a Mermaid diagram
- Saves to `graph_visualization.mmd`
- Optionally generates PNG (if graphviz installed)

**View the Mermaid diagram:**
1. Copy the output from the script
2. Go to https://mermaid.live/
3. Paste and view the interactive diagram

## Method 2: LangGraph Studio (Best for Development)

**LangGraph Studio** is the official IDE for visualizing and debugging LangGraph agents.

**Install and run:**
```bash
cd backend/langgraph-voice-call-agent
uv run langgraph studio
```

**Then open:** http://localhost:8123

**Features:**
- ✅ Interactive graph visualization
- ✅ Step through execution
- ✅ Inspect state at each step
- ✅ Debug tool calls
- ✅ Test your agent

## Method 3: Using LangGraph's Built-in Methods

You can also visualize programmatically:

```python
from src.langgraph.agent import agent

# Get the graph
graph = agent.get_graph()

# Print structure
print("Nodes:", graph.nodes)
print("Edges:", graph.edges)

# Generate Mermaid (if available)
mermaid = graph.draw_mermaid()
print(mermaid)
```

## Method 4: Online LangGraph Visualizer

**LangVis** - Web-based visualizer:
1. Go to https://www.langvis.com/
2. Load a template or import your graph
3. Visualize and inspect

## Understanding Your Graph

Your agent uses `create_react_agent`, which creates a **ReAct pattern**:

```
┌─────────┐
│  Agent  │ ← Main reasoning node
└────┬────┘
     │
     ▼
┌─────────┐
│  Tools  │ ← Tool execution (add_todo, list_todos, etc.)
└────┬────┘
     │
     ▼
┌─────────┐
│  Agent  │ ← Returns to agent with tool results
└─────────┘
```

**ReAct Pattern:**
- **Reasoning**: Agent decides what to do
- **Acting**: Calls tools
- **Observing**: Gets tool results
- **Loop**: Repeats until done

## Quick Start

**Simplest way:**
```bash
cd backend/langgraph-voice-call-agent
uv run python visualize_graph.py
```

Then copy the Mermaid output to https://mermaid.live/

**Best way (for development):**
```bash
cd backend/langgraph-voice-call-agent
uv run langgraph studio
```

Open http://localhost:8123 and explore your graph interactively!

