"""
setup_db.py — Create and populate the local portfolio SQLite database.
Run once:  python setup_db.py
"""

import sqlite3, pathlib

DB_PATH = pathlib.Path(__file__).parent / "my_rentals.db"


def create_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Properties table ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id              INTEGER PRIMARY KEY,
            name            TEXT    NOT NULL,
            address         TEXT    NOT NULL,
            city            TEXT    NOT NULL,
            state           TEXT    NOT NULL,
            property_type   TEXT    NOT NULL,
            bedrooms        INTEGER NOT NULL,
            bathrooms       REAL    NOT NULL,
            max_guests      INTEGER NOT NULL,
            nightly_rate    REAL    NOT NULL,
            cleaning_fee    REAL    NOT NULL,
            avg_occupancy   REAL    NOT NULL,   -- 0.0 – 1.0
            avg_rating      REAL,
            total_reviews   INTEGER DEFAULT 0,
            last_month_revenue REAL DEFAULT 0,
            status          TEXT    DEFAULT 'active',
            owner_name      TEXT,
            owner_email     TEXT
        )
    """)

    # ── Monthly performance table ─────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_performance (
            id           INTEGER PRIMARY KEY,
            property_id  INTEGER NOT NULL,
            month        TEXT    NOT NULL,       -- e.g. '2025-01'
            revenue      REAL    NOT NULL,
            occupancy    REAL    NOT NULL,
            bookings     INTEGER NOT NULL,
            avg_nightly  REAL    NOT NULL,
            expenses     REAL    DEFAULT 0,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)

    # ── Insert mock properties ────────────────────────────────────────
    properties = [
        (1, "Maple Street Retreat", "123 Maple St", "Austin", "TX",
         "Entire home", 3, 2.0, 8, 225.00, 85.00, 0.72, 4.81, 47,
         4860.00, "active", "Sarah Chen", "sarah.chen@email.com"),

        (2, "Downtown Loft", "456 Congress Ave", "Austin", "TX",
         "Entire apartment", 1, 1.0, 3, 165.00, 50.00, 0.85, 4.93, 112,
         4207.50, "active", "Sarah Chen", "sarah.chen@email.com"),

        (3, "Lakeside Bungalow", "789 Lake Austin Blvd", "Austin", "TX",
         "Entire home", 4, 3.0, 10, 310.00, 120.00, 0.61, 4.67, 29,
         5673.00, "active", "Marcus Webb", "marcus.webb@email.com"),

        (4, "South Congress Studio", "1010 S Congress Ave", "Austin", "TX",
         "Private room", 1, 1.0, 2, 89.00, 30.00, 0.91, 4.88, 203,
         2430.60, "active", "Sarah Chen", "sarah.chen@email.com"),

        (5, "Hill Country Villa", "2200 Barton Creek Dr", "Austin", "TX",
         "Entire home", 5, 4.0, 12, 475.00, 200.00, 0.52, 4.45, 15,
         7410.00, "active", "Marcus Webb", "marcus.webb@email.com"),
    ]

    cur.executemany("""
        INSERT OR REPLACE INTO properties
        (id, name, address, city, state, property_type, bedrooms, bathrooms,
         max_guests, nightly_rate, cleaning_fee, avg_occupancy, avg_rating,
         total_reviews, last_month_revenue, status, owner_name, owner_email)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, properties)

    # ── Insert 6 months of performance data ───────────────────────────
    perf_data = [
        # Property 1 – Maple Street Retreat
        (1, "2025-07", 5100.00, 0.75, 7, 230.00, 680.00),
        (1, "2025-08", 5400.00, 0.78, 8, 225.00, 710.00),
        (1, "2025-09", 4200.00, 0.65, 6, 215.00, 620.00),
        (1, "2025-10", 3800.00, 0.58, 5, 210.00, 590.00),
        (1, "2025-11", 4500.00, 0.70, 6, 225.00, 650.00),
        (1, "2025-12", 4860.00, 0.72, 7, 225.00, 700.00),
        # Property 2 – Downtown Loft
        (2, "2025-07", 4100.00, 0.82, 12, 170.00, 420.00),
        (2, "2025-08", 4350.00, 0.87, 13, 165.00, 430.00),
        (2, "2025-09", 3900.00, 0.78, 11, 160.00, 400.00),
        (2, "2025-10", 3600.00, 0.75, 10, 155.00, 380.00),
        (2, "2025-11", 4000.00, 0.82, 12, 165.00, 410.00),
        (2, "2025-12", 4207.50, 0.85, 12, 165.00, 425.00),
        # Property 3 – Lakeside Bungalow
        (3, "2025-07", 6200.00, 0.68, 5, 320.00, 850.00),
        (3, "2025-08", 6800.00, 0.74, 6, 315.00, 880.00),
        (3, "2025-09", 5100.00, 0.55, 4, 300.00, 780.00),
        (3, "2025-10", 4600.00, 0.48, 3, 295.00, 720.00),
        (3, "2025-11", 5200.00, 0.58, 4, 310.00, 800.00),
        (3, "2025-12", 5673.00, 0.61, 5, 310.00, 830.00),
        # Property 4 – South Congress Studio
        (4, "2025-07", 2500.00, 0.93, 22, 92.00, 310.00),
        (4, "2025-08", 2600.00, 0.95, 23, 90.00, 320.00),
        (4, "2025-09", 2300.00, 0.88, 20, 88.00, 290.00),
        (4, "2025-10", 2100.00, 0.82, 18, 85.00, 270.00),
        (4, "2025-11", 2350.00, 0.90, 21, 89.00, 300.00),
        (4, "2025-12", 2430.60, 0.91, 21, 89.00, 305.00),
        # Property 5 – Hill Country Villa
        (5, "2025-07", 8200.00, 0.58, 4, 480.00, 1100.00),
        (5, "2025-08", 8800.00, 0.62, 4, 490.00, 1150.00),
        (5, "2025-09", 6500.00, 0.45, 3, 460.00, 980.00),
        (5, "2025-10", 5800.00, 0.40, 3, 445.00, 920.00),
        (5, "2025-11", 6900.00, 0.50, 3, 470.00, 1020.00),
        (5, "2025-12", 7410.00, 0.52, 4, 475.00, 1080.00),
    ]

    cur.executemany("""
        INSERT OR REPLACE INTO monthly_performance
        (property_id, month, revenue, occupancy, bookings, avg_nightly, expenses)
        VALUES (?,?,?,?,?,?,?)
    """, perf_data)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print(f"    -> 5 properties with 6 months of performance history each")


if __name__ == "__main__":
    create_database()
