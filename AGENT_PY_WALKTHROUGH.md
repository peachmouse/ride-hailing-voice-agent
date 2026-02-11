# 📝 Step-by-Step Walkthrough of `agent.py`

This document walks through every line of `backend/langgraph-voice-call-agent/src/langgraph/agent.py`, explaining what each part does and why it's there.

---

## 📁 File Overview

**Location**: `backend/langgraph-voice-call-agent/src/langgraph/agent.py`  
**Purpose**: Defines the LangGraph agent with tools for managing a todo list  
**Total Lines**: 129

---

## 🔍 Step-by-Step Breakdown

### **Lines 1-6: Imports**

```python
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
```

**What's happening:**

1. **`from typing import TypedDict`** (Line 1)
   - Imports `TypedDict` for type-safe dictionaries
   - Used to define the `Todo` type (line 13)

2. **`from dotenv import load_dotenv`** (Line 2)
   - Imports function to load environment variables from `.env` file
   - Used on line 7 to load API keys (like `OPENAI_API_KEY`)

3. **`from langgraph.prebuilt import create_react_agent`** (Line 3)
   - Imports the prebuilt ReAct agent creator
   - This is the function that builds your entire graph (used on line 108)

4. **`from langchain_openai import ChatOpenAI`** (Line 4)
   - Imports the OpenAI LLM wrapper
   - Used to create the language model (line 109)

5. **`from langgraph.types import interrupt`** (Line 5)
   - Imports the `interrupt` function for pausing execution
   - Used in `delete_todo` to ask for user confirmation (line 90)

---

### **Line 7: Load Environment Variables**

```python
load_dotenv()
```

**What's happening:**
- Loads all variables from `.env` file into the environment
- Makes `OPENAI_API_KEY` available for `ChatOpenAI` to use
- Must be called before creating the `ChatOpenAI` instance

**Why it's needed:**
- `ChatOpenAI` automatically reads `OPENAI_API_KEY` from environment
- Keeps API keys out of your code (security best practice)

---

### **Lines 9-10: Global Todo Storage**

```python
# In-memory storage for todos
todos = []
```

**What's happening:**
- Creates a global list to store todos
- This is **in-memory** storage (lost when program restarts)
- Each todo will be a dictionary with `id`, `task`, and `completed` fields

**Note**: In a real application, you'd use a database instead of a global list.

---

### **Lines 12-16: Todo Type Definition**

```python
# Define Todo type
class Todo(TypedDict):
    id: int
    task: str
    completed: bool
```

**What's happening:**
- Defines the structure of a todo item using `TypedDict`
- This provides type hints for better code clarity and IDE support

**Structure:**
- `id`: Unique identifier (integer)
- `task`: The todo text (string)
- `completed`: Whether it's done (boolean)

**Example todo:**
```python
{
    "id": 1,
    "task": "buy groceries",
    "completed": False
}
```

---

### **Lines 18-32: `add_todo` Tool Function**

```python
# Tool definitions
def add_todo(task: str) -> str:
    """Add a new task to the todo list.
    
    Args:
        task: The task to add to the todo list
        
    Returns:
        Confirmation message
    """
    global todos
    todo_id = len(todos) + 1
    new_todo = {"id": todo_id, "task": task, "completed": False}
    todos.append(new_todo)
    return f"Added todo #{todo_id}: {task}"
```

**What's happening step by step:**

1. **Function signature** (Line 19)
   - `def add_todo(task: str) -> str:`
   - Takes a `task` string parameter
   - Returns a confirmation string

2. **Docstring** (Lines 20-27)
   - Describes what the function does
   - **Important**: LangGraph uses docstrings to tell the LLM what tools do!
   - The LLM reads this to understand when to call this tool

3. **`global todos`** (Line 28)
   - Accesses the global `todos` list
   - Needed to modify the list from inside the function

4. **Generate ID** (Line 29)
   - `todo_id = len(todos) + 1`
   - Creates a unique ID based on current list length
   - First todo gets ID 1, second gets ID 2, etc.

5. **Create todo** (Line 30)
   - Creates a dictionary matching the `Todo` type
   - Sets `completed: False` by default

6. **Add to list** (Line 31)
   - Appends the new todo to the global `todos` list

7. **Return confirmation** (Line 32)
   - Returns a message that the LLM will see
   - Example: `"Added todo #1: buy groceries"`

**How the agent uses this:**
- User: "Add buy groceries to my todo list"
- LLM calls: `add_todo("buy groceries")`
- Function executes and returns: `"Added todo #1: buy groceries"`
- LLM responds: "I've added 'buy groceries' to your todo list!"

---

### **Lines 34-50: `list_todos` Tool Function**

```python
def list_todos() -> list[Todo]:
    """List all todos in the todo list.
    
    Returns:
        Formatted list of todos
    """
    global todos
    if not todos:
        return []
    
    return todos
    
    result = "Here's your todo list:\n"
    for todo in todos:
        status = "✅" if todo["completed"] else "⬜️"
        result += f"{status} {todo['id']}. {todo['task']}\n"
    return result
```

**What's happening:**

1. **Function signature** (Line 34)
   - `def list_todos() -> list[Todo]:`
   - Takes no parameters
   - Returns a list of `Todo` dictionaries

2. **Docstring** (Lines 35-39)
   - Describes the function
   - LLM reads this to know when to call it

3. **Check if empty** (Lines 41-42)
   - If `todos` is empty, return empty list
   - Prevents errors when there are no todos

4. **Return todos** (Line 44)
   - Returns the raw list of todos
   - **Note**: Lines 46-50 are **unreachable code** (dead code)
   - They would format the output nicely, but `return todos` on line 44 exits first

**Bug/Unused Code:**
- Lines 46-50 format todos nicely but are never executed
- The function returns on line 44 before reaching them
- This could be fixed by removing line 44 or the formatting code

**How the agent uses this:**
- User: "Show me my todos"
- LLM calls: `list_todos()`
- Function returns: `[{"id": 1, "task": "buy groceries", "completed": False}, ...]`
- LLM formats and responds: "Here are your todos: 1. buy groceries, ..."

---

### **Lines 52-66: `complete_todo` Tool Function**

```python
def complete_todo(todo_id: int) -> str:
    """Mark a todo as completed.
    
    Args:
        todo_id: The ID of the todo to mark as complete
        
    Returns:
        Confirmation message
    """
    global todos
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = True
            return f"Marked todo #{todo_id} as completed."
    return f"Todo with ID {todo_id} not found."
```

**What's happening:**

1. **Function signature** (Line 52)
   - Takes `todo_id` (integer) to identify which todo to complete
   - Returns a confirmation string

2. **Search loop** (Lines 62-65)
   - Iterates through all todos
   - Finds the one with matching `id`
   - Sets `completed = True`
   - Returns success message

3. **Not found case** (Line 66)
   - If no todo matches the ID, returns error message
   - This handles invalid IDs gracefully

**How the agent uses this:**
- User: "Mark todo 1 as done"
- LLM calls: `complete_todo(1)`
- Function finds todo #1, sets `completed = True`
- Returns: `"Marked todo #1 as completed."`
- LLM responds: "I've marked todo #1 as completed!"

---

### **Lines 68-104: `delete_todo` Tool Function**

```python
def delete_todo(todo_id: int) -> str:
    """Delete a todo from the list.
    
    Args:
        todo_id: The ID of the todo to delete
        
    Returns:
        Confirmation message
    """
    global todos
    
    # First find the todo item
    todo_to_delete = None
    for todo in todos:
        if todo["id"] == todo_id:
            todo_to_delete = todo
            break
    
    if not todo_to_delete:
        return f"Todo with ID {todo_id} not found."
    
    # Ask for confirmation before deletion
    confirmation = interrupt(f"Are you sure you want to delete todo #{todo_id}: '{todo_to_delete['task']}'? (yes/no)")
    
    # Process based on confirmation - handle both string and list responses
    # Convert confirmation to string if it's a list or other type
    confirmation_str = str(confirmation)
    if isinstance(confirmation, list) and len(confirmation) > 0:
        confirmation_str = str(confirmation[0])
    
    if confirmation_str.lower() in ["yes", "y", "true"]:
        for i, todo in enumerate(todos):
            if todo["id"] == todo_id:
                del todos[i]
                return f"Deleted todo #{todo_id}."
    else:
        return f"Deletion of todo #{todo_id} cancelled."
```

**What's happening step by step:**

1. **Find the todo** (Lines 80-84)
   - Searches for the todo with matching ID
   - Stores it in `todo_to_delete` for later use

2. **Check if found** (Lines 86-87)
   - If not found, return error message immediately

3. **Ask for confirmation** (Line 90)
   - **`interrupt()`** is a LangGraph function that pauses execution
   - Shows the user: `"Are you sure you want to delete todo #1: 'buy groceries'? (yes/no)"`
   - Waits for user response before continuing
   - This is a **safety feature** to prevent accidental deletions

4. **Handle confirmation response** (Lines 92-96)
   - Converts confirmation to string
   - Handles if it comes as a list (some edge cases)
   - Extracts first element if it's a list

5. **Delete or cancel** (Lines 98-104)
   - If user says "yes", "y", or "true":
     - Finds the todo in the list by index
     - Deletes it using `del todos[i]`
     - Returns success message
   - Otherwise:
     - Returns cancellation message
     - Todo remains in the list

**How the agent uses this:**
- User: "Delete todo 1"
- LLM calls: `delete_todo(1)`
- Function pauses and asks: "Are you sure you want to delete todo #1: 'buy groceries'? (yes/no)"
- User: "yes"
- Function deletes todo and returns: `"Deleted todo #1."`
- LLM responds: "I've deleted todo #1."

**Key Feature**: The `interrupt()` function allows the agent to pause and ask for user input mid-execution!

---

### **Lines 107-129: Create the ReAct Agent**

```python
# Create the ReAct agent
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4.1-nano"),
    tools=[add_todo, list_todos, complete_todo, delete_todo],
    prompt="""You are a helpful todo list manager with vision capabilities.
      You can help users manage their tasks with the following tools:
      - add_todo: Add a new task to the list
      - list_todos: Show all tasks
      - complete_todo: Mark a task as done
      - delete_todo: Remove a task from the list

      You can also see and understand visual content from the user's camera or screen sharing.
      When users share their screen or camera, you can:
      - Describe what you see
      - Help with tasks related to the visual content
      - Provide guidance based on what's displayed
      - Answer questions about documents, images, or applications shown

      Always use the appropriate tool when needed. Be concise but friendly in your responses.
      If you receive visual input, acknowledge it and provide helpful insights.
      """,
    name="todo_agent"
  )
```

**What's happening:**

1. **`create_react_agent()`** (Line 108)
   - This is the **main function** that builds your entire graph
   - It creates nodes, edges, routing logic - everything!
   - Returns a compiled LangGraph ready to use

2. **`model=ChatOpenAI(model="gpt-4.1-nano")`** (Line 109)
   - Creates the LLM that powers the agent
   - Uses OpenAI's GPT-4.1-nano model
   - Automatically reads `OPENAI_API_KEY` from environment (loaded by `load_dotenv()`)

3. **`tools=[...]`** (Line 110)
   - Passes all four tool functions to the agent
   - The agent can now call these functions when needed
   - LangGraph automatically converts them to tool definitions

4. **`prompt="""..."""`** (Lines 111-127)
   - This is the **system prompt** that instructs the agent
   - Tells the agent:
     - What it is (todo list manager)
     - What tools it has
     - How to use them
     - That it can see visual content (camera/screen sharing)
   - This prompt is sent to the LLM on every conversation turn

5. **`name="todo_agent"`** (Line 128)
   - Names the agent "todo_agent"
   - Used when registering with LangGraph server
   - Referenced in `langgraph.json` as `"todo_agent"`

**What `create_react_agent()` does internally:**
- Creates a graph with nodes: `agent`, `tools`
- Sets up routing: `agent → tools → agent` (loop)
- Handles state management (conversation history)
- Compiles everything into a ready-to-use graph

**The result:**
- `agent` is now a compiled LangGraph that can:
  - Accept user messages
  - Decide which tools to call
  - Execute tools
  - Generate responses
  - Maintain conversation state

---

## 🔄 Complete Flow Example

Let's trace through a complete interaction:

**User says**: "Add buy groceries to my todo list"

1. **Message arrives** → LangGraph receives `HumanMessage("Add buy groceries...")`

2. **Agent node executes**:
   - Calls `ChatOpenAI` with the message
   - LLM decides to call `add_todo` tool
   - Returns `AIMessage` with `tool_calls=[{"name": "add_todo", "args": {"task": "buy groceries"}}]`

3. **Routing** → Goes to `tools` node (because tool_calls exist)

4. **Tools node executes**:
   - Calls `add_todo("buy groceries")`
   - Function executes (lines 28-32):
     - Creates todo with ID 1
     - Adds to `todos` list
     - Returns `"Added todo #1: buy groceries"`
   - Creates `ToolMessage` with the result

5. **Back to agent node**:
   - LLM sees the tool result
   - Generates final response: `"I've added 'buy groceries' to your todo list!"`

6. **Routing** → Goes to `END` (no more tool_calls)

7. **Done!** User receives the response.

---

## 📊 Summary

**File Structure:**
1. **Imports** (Lines 1-6) - Load dependencies
2. **Environment** (Line 7) - Load API keys
3. **Storage** (Lines 9-10) - Global todos list
4. **Type Definition** (Lines 12-16) - Todo structure
5. **Tool Functions** (Lines 18-104) - Four tools:
   - `add_todo` - Add a task
   - `list_todos` - List all tasks
   - `complete_todo` - Mark as done
   - `delete_todo` - Delete (with confirmation)
6. **Agent Creation** (Lines 107-129) - Build the graph

**Key Concepts:**
- **Tools** are just Python functions with docstrings
- **LangGraph** automatically converts them to tools the LLM can use
- **`create_react_agent()`** builds the entire graph for you
- **`interrupt()`** allows pausing for user input
- **Global state** (`todos`) persists during the conversation

**This file is the "brain" of your agent** - it defines what the agent can do! 🧠

