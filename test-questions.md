# STR Supervisor Agent — Test Questions

Safe questions organized by which path they exercise. The supervisor has all
portfolio data baked into its system prompt, so most property questions are
answered directly (no tool calls). Only Market Scout and Comms Assistant
require tool delegation.

---

## 1. Direct Portfolio Questions (no tools, instant)

These are answered by the supervisor from its embedded data. Fastest path.

- "How many properties do we manage?"
- "What's our total revenue last month?"
- "Which property has the highest occupancy?"
- "What's the nightly rate for the Downtown Loft?"
- "How many bedrooms does the Lakeside Bungalow have?"
- "Which properties does Sarah Chen own?"
- "What's our average portfolio rating?"
- "Which property is underperforming?"
- "Compare the Downtown Loft and South Congress Studio."
- "What's the revenue trend for Hill Country Villa over the last six months?"
- "Which property has the most reviews?"
- "What's our most expensive listing?"

## 2. Market Scout Questions (Airbnb MCP, ~15s)

These trigger `call_market_scout` which initializes the Airbnb MCP server on
first use. Expect a delay on the first call.

- "What are competitors charging for 3-bedroom homes in Austin?"
- "Search Airbnb for listings near South Congress under $150 a night."
- "How does our Downtown Loft pricing compare to similar listings on Airbnb?"
- "Find me luxury Airbnb listings in Austin that sleep 10 or more guests."
- "What's the going rate for a 1-bedroom apartment downtown on Airbnb?"

## 3. Comms Assistant Questions (message drafting, fast)

These trigger `call_comms_assistant` to draft a message.

- "Draft a Slack message to Sarah Chen about the Downtown Loft's strong performance."
- "Write an email to Marcus Webb suggesting a price reduction for the Hill Country Villa."
- "Draft a summary report of last month's portfolio performance for the team."
- "Write a message to the operations team about the Lakeside Bungalow's low occupancy."
- "Draft a Slack message to Marcus about raising the Lakeside Bungalow rate for spring."

## 4. Multi-Step Workflows (combine agents)

These should trigger multiple tool calls in sequence.

- "Compare our Maple Street Retreat to similar Airbnb listings and draft a pricing recommendation email to Sarah Chen."
- "Check what competitors charge for 5-bedroom homes in Austin, then draft a message to Marcus Webb about adjusting the Hill Country Villa price."
- "Find comparable listings for the South Congress Studio on Airbnb and write a Slack update to Sarah."

## 5. General Conversation (no tools, instant)

Sanity checks that the agent handles casual talk gracefully.

- "Hey, who are you?"
- "What can you help me with?"
- "Thanks, that's all for now."
