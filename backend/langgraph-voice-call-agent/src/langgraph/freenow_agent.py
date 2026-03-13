"""
freenow_agent.py — FreeNow Ride-Hailing Booking Agent for LangGraph Server.

AI-native voice agent: extracts multiple slots from a single utterance,
disambiguates locations, estimates fares proactively, and handles
multi-intent conversations — things an IVR can never do.
"""

import random
import string
import time
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


# ── Mock data ─────────────────────────────────────────────────────────

_DRIVER_NAMES = [
    "Tomasz Kowalski", "Anna Nowak", "Piotr Wiśniewski",
    "Katarzyna Wójcik", "Marek Kamiński", "Ewa Lewandowska",
]

_VEHICLES = [
    "Toyota Camry (silver)", "Škoda Octavia (black)", "Hyundai i30 (white)",
    "Volkswagen Passat (dark blue)", "Kia Ceed (red)", "Ford Focus (grey)",
]

# Warsaw-area location database for disambiguation
_LOCATIONS = {
    "airport": [
        {"name": "Warsaw Chopin Airport (WAW)", "address": "ul. Żwirki i Wigury 1, Warszawa", "type": "airport"},
        {"name": "Warsaw Modlin Airport", "address": "Nowy Dwór Mazowiecki", "type": "airport"},
    ],
    "station": [
        {"name": "Warszawa Centralna (Central Station)", "address": "al. Jerozolimskie 54, Warszawa", "type": "train_station"},
        {"name": "Warszawa Zachodnia (West Station)", "address": "al. Jerozolimskie 144, Warszawa", "type": "train_station"},
        {"name": "Warszawa Wschodnia (East Station)", "address": "ul. Lubelska 1, Warszawa", "type": "train_station"},
    ],
    "old town": [
        {"name": "Old Town Market Square (Rynek Starego Miasta)", "address": "Rynek Starego Miasta, Warszawa", "type": "landmark"},
    ],
    "palace": [
        {"name": "Palace of Culture and Science", "address": "pl. Defilad 1, Warszawa", "type": "landmark"},
        {"name": "Wilanów Palace", "address": "ul. Stanisława Kostki Potockiego 10/16, Warszawa", "type": "landmark"},
        {"name": "Royal Castle", "address": "pl. Zamkowy 4, Warszawa", "type": "landmark"},
    ],
    "mall": [
        {"name": "Złote Tarasy", "address": "ul. Złota 59, Warszawa", "type": "shopping"},
        {"name": "Arkadia Shopping Centre", "address": "al. Jana Pawła II 82, Warszawa", "type": "shopping"},
        {"name": "Galeria Mokotów", "address": "ul. Wołoska 12, Warszawa", "type": "shopping"},
    ],
    "university": [
        {"name": "University of Warsaw (Main Campus)", "address": "ul. Krakowskie Przedmieście 26/28", "type": "education"},
        {"name": "Warsaw University of Technology", "address": "pl. Politechniki 1, Warszawa", "type": "education"},
    ],
    "hotel": [
        {"name": "Marriott Hotel Warsaw", "address": "al. Jerozolimskie 65/79, Warszawa", "type": "hotel"},
        {"name": "Hotel Bristol Warsaw", "address": "ul. Krakowskie Przedmieście 42/44", "type": "hotel"},
        {"name": "InterContinental Warszawa", "address": "ul. Emilii Plater 49, Warszawa", "type": "hotel"},
    ],
}

# Distance heuristics (in km) between common area pairs for fare estimation
_DISTANCE_MATRIX = {
    ("centrum", "chopin airport"): 11,
    ("centrum", "modlin airport"): 40,
    ("centrum", "old town"): 3,
    ("centrum", "mokotów"): 5,
    ("centrum", "praga"): 4,
    ("centrum", "wilanów"): 12,
    ("centrum", "ursynów"): 10,
    ("centrum", "wola"): 3,
    ("centrum", "żoliborz"): 5,
    ("chopin airport", "old town"): 13,
    ("chopin airport", "mokotów"): 6,
    ("chopin airport", "praga"): 15,
    ("central station", "chopin airport"): 10,
    ("central station", "modlin airport"): 42,
    ("central station", "old town"): 3,
}

# Ride status progression — each booking steps through these over time
_STATUS_PROGRESSION = [
    "confirmed",
    "driver_assigned",
    "driver_en_route",
    "arriving",
    "in_progress",
    "completed",
]

# In-memory store for booked rides (reset each server restart)
_bookings: dict[str, dict] = {}


# ── Tools ─────────────────────────────────────────────────────────────

@tool
def book_ride(pickup: str, dropoff: str, scheduled_time: Optional[str] = None) -> dict:
    """Book a FreeNow ride. Call this after the user has confirmed pickup, dropoff, and timing.

    Args:
        pickup: The pickup address or location name.
        dropoff: The dropoff address or location name.
        scheduled_time: Optional scheduled time (e.g. "in 30 minutes", "3:00 PM"). If None, ride is booked for now.

    Returns:
        Booking confirmation with booking ID, ETA, driver name, and vehicle.
    """
    booking_id = "FN-" + "".join(random.choices(string.digits, k=5))
    eta = random.randint(3, 12)
    driver = random.choice(_DRIVER_NAMES)
    vehicle = random.choice(_VEHICLES)

    _bookings[booking_id] = {
        "booking_id": booking_id,
        "pickup": pickup,
        "dropoff": dropoff,
        "scheduled_time": scheduled_time or "now",
        "eta_minutes": eta,
        "driver_name": driver,
        "vehicle": vehicle,
        "status": "confirmed",
        "booked_at": time.time(),
    }

    return {
        "booking_id": booking_id,
        "eta_minutes": eta,
        "driver_name": driver,
        "vehicle": vehicle,
        "pickup": pickup,
        "dropoff": dropoff,
        "scheduled_time": scheduled_time or "now",
    }


@tool
def check_ride_status(booking_id: str) -> dict:
    """Check the status of an existing FreeNow ride booking.

    Args:
        booking_id: The booking ID (e.g. "FN-12345").

    Returns:
        Current ride status including driver info and ETA.
    """
    if booking_id in _bookings:
        booking = _bookings[booking_id]

        # Time-aware status progression: advance based on elapsed time
        elapsed = time.time() - booking.get("booked_at", time.time())
        elapsed_minutes = elapsed / 60

        if elapsed_minutes < 1:
            status = "confirmed"
            message = f"Your ride is confirmed. Looking for a driver near {booking['pickup']}."
            eta = random.randint(4, 10)
        elif elapsed_minutes < 3:
            status = "driver_assigned"
            message = f"Driver {booking['driver_name']} has been assigned in a {booking['vehicle']}. They're heading to your pickup."
            eta = random.randint(3, 8)
        elif elapsed_minutes < 6:
            status = "driver_en_route"
            message = f"Your driver {booking['driver_name']} is on the way in a {booking['vehicle']}."
            eta = random.randint(2, 5)
        elif elapsed_minutes < 10:
            status = "arriving"
            message = f"Your driver {booking['driver_name']} is arriving now! Look for a {booking['vehicle']}."
            eta = 1
        elif elapsed_minutes < 30:
            status = "in_progress"
            remaining = max(1, int(25 - elapsed_minutes))
            message = f"You're on your way to {booking['dropoff']} with {booking['driver_name']}. About {remaining} minutes remaining."
            eta = remaining
        else:
            status = "completed"
            message = f"Your ride to {booking['dropoff']} is complete. Thanks for riding with FreeNow!"
            eta = 0

        # Update stored status
        booking["status"] = status

        return {
            "booking_id": booking_id,
            "pickup": booking["pickup"],
            "dropoff": booking["dropoff"],
            "status": status,
            "message": message,
            "eta_minutes": eta,
            "driver_name": booking["driver_name"],
            "vehicle": booking["vehicle"],
        }

    return {
        "booking_id": booking_id,
        "status": "not_found",
        "message": f"No booking found with ID {booking_id}. Please double-check the booking ID.",
    }


@tool
def estimate_fare(pickup: str, dropoff: str) -> dict:
    """Estimate the fare and travel time for a ride between two locations.
    Use this proactively to give the user pricing info before they commit to a booking.

    Args:
        pickup: The pickup address or location name.
        dropoff: The dropoff address or location name.

    Returns:
        Estimated fare range and travel duration.
    """
    # Try to look up distance from the matrix (fuzzy match on keywords)
    distance_km = None
    pickup_lower = pickup.lower()
    dropoff_lower = dropoff.lower()

    for (a, b), km in _DISTANCE_MATRIX.items():
        if (a in pickup_lower or a in dropoff_lower) and (b in pickup_lower or b in dropoff_lower):
            distance_km = km
            break
        if (b in pickup_lower or b in dropoff_lower) and (a in pickup_lower or a in dropoff_lower):
            distance_km = km
            break

    # Fallback: random reasonable distance for Warsaw
    if distance_km is None:
        distance_km = random.randint(4, 18)

    # Fare calculation: base fare + per-km rate with some variance
    base_fare = 8.0  # PLN
    per_km = 3.0  # PLN
    estimated = base_fare + (per_km * distance_km)
    low = round(estimated * 0.85, 2)
    high = round(estimated * 1.20, 2)
    duration_min = max(5, int(distance_km * 2.2) + random.randint(-3, 5))

    return {
        "pickup": pickup,
        "dropoff": dropoff,
        "estimated_distance_km": distance_km,
        "fare_range_pln": {"low": low, "high": high},
        "estimated_duration_minutes": duration_min,
        "currency": "PLN",
        "note": "Final fare depends on traffic and exact route.",
    }


@tool
def get_nearby_locations(query: str) -> dict:
    """Search for locations matching a query in the Warsaw area.
    Use this when the user mentions an ambiguous place name (like "airport", "station",
    "mall", "hotel") to offer them specific options.

    Args:
        query: The location search term (e.g. "airport", "train station", "hotel").

    Returns:
        List of matching locations with names and addresses.
    """
    query_lower = query.lower()
    matches = []

    for keyword, locations in _LOCATIONS.items():
        if keyword in query_lower or query_lower in keyword:
            matches.extend(locations)

    # Also do a fuzzy search across all location names
    if not matches:
        for locations in _LOCATIONS.values():
            for loc in locations:
                if query_lower in loc["name"].lower() or query_lower in loc.get("address", "").lower():
                    matches.append(loc)

    if matches:
        return {
            "query": query,
            "results_count": len(matches),
            "locations": matches,
        }

    return {
        "query": query,
        "results_count": 0,
        "locations": [],
        "note": f"No known landmarks matching '{query}'. The user might mean a specific street address — ask them to clarify.",
    }


# ── System prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a FreeNow ride-hailing assistant — warm, helpful, and smart. You're a VOICE agent, \
so keep every response to 1-3 short sentences.

CORE PRINCIPLE: Be intelligent, not mechanical. An IVR asks one rigid question at a time. \
You understand context, extract multiple pieces of info from a single sentence, and think ahead.

WHAT MAKES YOU SMART:
- If the user says "Take me from Central Station to the airport at 3pm", you already have \
pickup, dropoff, AND time — don't ask for them one by one. Jump straight to confirming.
- If a location is ambiguous (e.g. "the airport", "the station"), use get_nearby_locations \
to find options and ask which one they mean.
- Proactively call estimate_fare before booking so the user knows the price. Share the fare \
range naturally: "That should run about 35 to 45 złoty, around 20 minutes."
- If the user changes their mind mid-conversation ("actually, pick me up at home instead"), \
just update the relevant detail — don't restart the whole flow.
- Handle multiple requests in one conversation: "Book me a ride AND check booking FN-12345" — \
do both.
- If the user asks something off-topic, briefly acknowledge it, then steer back.

BOOKING FLOW:
1. Understand what the user needs (book a ride, check status, get a fare estimate, or other).
2. Gather whatever info you're still missing — but only ask for what you don't already know.
3. Confirm the full ride details with the user (pickup, dropoff, time, estimated fare).
4. Call book_ride, then share the confirmation: ETA, driver name, vehicle, booking ID.

TOOLS AT YOUR DISPOSAL:
- book_ride: Book a confirmed ride.
- check_ride_status: Look up an existing booking.
- estimate_fare: Get fare range + duration between two points. Use this proactively!
- get_nearby_locations: Disambiguate vague places like "airport" or "station" or "mall".

RULES:
- NEVER output JSON, raw data, or tool details. Speak naturally.
- Always confirm details before calling book_ride.
- After booking, mention the booking ID so they can check status later.
- For things you can't handle (complaints, payments, account issues), say you'll transfer them \
to a human agent.
- Be warm and slightly casual — like a helpful local friend, not a corporate script."""


# ── Agent ─────────────────────────────────────────────────────────────

agent = create_react_agent(
    ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,
        max_tokens=1024,
    ),
    tools=[book_ride, check_ride_status, estimate_fare, get_nearby_locations],
    prompt=SYSTEM_PROMPT,
)
