"""
portfolio_mcp_server.py — MCP Server for the internal property portfolio.
Exposes SQLite data as MCP tools that the Portfolio Analyst agent can call.

Run standalone for testing:  python portfolio_mcp_server.py
Used by agents via stdio transport through langchain-mcp-adapters.
"""

import json
import sqlite3
import pathlib
from mcp.server.fastmcp import FastMCP

DB_PATH = pathlib.Path(__file__).parent / "my_rentals.db"

mcp = FastMCP("PortfolioPMS")


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read-only query and return rows as dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ── Tool 1: List all properties ──────────────────────────────────────

@mcp.tool()
def list_portfolio_properties() -> str:
    """
    List all properties in the portfolio with their key details:
    name, address, nightly rate, occupancy, rating, and status.
    Use this to get an overview of all managed properties.
    """
    rows = _query("""
        SELECT id, name, address, city, state, property_type,
               bedrooms, bathrooms, max_guests, nightly_rate,
               cleaning_fee, avg_occupancy, avg_rating,
               total_reviews, last_month_revenue, status,
               owner_name, owner_email
        FROM properties
        ORDER BY id
    """)
    return json.dumps(rows, indent=2)


# ── Tool 2: Get a single property's details ──────────────────────────

@mcp.tool()
def get_property_details(property_id: int) -> str:
    """
    Get full details for a specific property by its ID.
    Returns name, address, pricing, occupancy, rating, owner info, etc.
    """
    rows = _query("SELECT * FROM properties WHERE id = ?", (property_id,))
    if not rows:
        return json.dumps({"error": f"No property found with id {property_id}"})
    return json.dumps(rows[0], indent=2)


# ── Tool 3: Search properties by address or name ─────────────────────

@mcp.tool()
def search_property(query: str) -> str:
    """
    Search for a property by name or address (partial match).
    Use this when the user refers to a property by address like '123 Maple St'
    or by name like 'Downtown Loft'.
    """
    rows = _query("""
        SELECT id, name, address, city, state, nightly_rate,
               avg_occupancy, avg_rating, last_month_revenue,
               owner_name, owner_email
        FROM properties
        WHERE name LIKE ? OR address LIKE ?
        ORDER BY id
    """, (f"%{query}%", f"%{query}%"))
    if not rows:
        return json.dumps({"message": f"No properties matching '{query}'"})
    return json.dumps(rows, indent=2)


# ── Tool 4: Get monthly performance history ──────────────────────────

@mcp.tool()
def get_performance_history(property_id: int, months: int = 6) -> str:
    """
    Get monthly performance history for a property.
    Returns revenue, occupancy rate, number of bookings, avg nightly rate,
    and expenses for the last N months.
    """
    rows = _query("""
        SELECT p.name, mp.month, mp.revenue, mp.occupancy,
               mp.bookings, mp.avg_nightly, mp.expenses
        FROM monthly_performance mp
        JOIN properties p ON p.id = mp.property_id
        WHERE mp.property_id = ?
        ORDER BY mp.month DESC
        LIMIT ?
    """, (property_id, months))
    if not rows:
        return json.dumps({"error": f"No performance data for property {property_id}"})
    return json.dumps(rows, indent=2)


# ── Tool 5: Portfolio summary / comparison ────────────────────────────

@mcp.tool()
def get_portfolio_summary() -> str:
    """
    Get a high-level summary of the entire portfolio:
    total properties, average occupancy, total revenue, avg nightly rate,
    and a per-property breakdown.
    """
    rows = _query("""
        SELECT
            COUNT(*)                          AS total_properties,
            ROUND(AVG(avg_occupancy), 2)      AS avg_occupancy,
            ROUND(SUM(last_month_revenue), 2) AS total_last_month_revenue,
            ROUND(AVG(nightly_rate), 2)       AS avg_nightly_rate,
            ROUND(AVG(avg_rating), 2)         AS avg_rating
        FROM properties
        WHERE status = 'active'
    """)
    summary = rows[0] if rows else {}

    per_prop = _query("""
        SELECT name, address, nightly_rate, avg_occupancy,
               last_month_revenue, avg_rating
        FROM properties
        WHERE status = 'active'
        ORDER BY last_month_revenue DESC
    """)
    summary["properties"] = per_prop
    return json.dumps(summary, indent=2)


# ── Tool 6: Run custom SQL (read-only, for advanced queries) ─────────

@mcp.tool()
def run_portfolio_query(sql_query: str) -> str:
    """
    Run a custom read-only SQL query against the portfolio database.
    Available tables: 'properties', 'monthly_performance'.
    Use this for advanced analytical queries like comparisons, aggregations,
    or trend analysis that the other tools don't cover.
    Only SELECT statements are allowed.
    """
    cleaned = sql_query.strip().upper()
    if not cleaned.startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed."})
    try:
        rows = _query(sql_query)
        return json.dumps(rows, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
