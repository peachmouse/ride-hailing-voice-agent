"""
Interactive CLI chat with the FreeNow agent via the LangGraph dev server.

Prerequisites:
  1. Start the LangGraph server:  uv run langgraph dev
  2. Run this script:             uv run python chat.py
"""

import uuid

from langgraph_sdk import get_sync_client


def main():
    client = get_sync_client(url="http://localhost:2024")
    thread = client.threads.create()
    thread_id = thread["thread_id"]
    print(f"Thread: {thread_id}")
    print("Type your message (Ctrl+C to quit)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue

        response = client.runs.wait(
            thread_id=thread_id,
            assistant_id="freenow_agent",
            input={"messages": [{"role": "user", "content": user_input}]},
        )

        # Last AI message
        for msg in reversed(response["messages"]):
            if msg["type"] == "ai" and msg.get("content"):
                print(f"Agent: {msg['content']}\n")
                break


if __name__ == "__main__":
    main()
