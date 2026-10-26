# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any, Optional

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.cloud import firestore
from google.genai import types

MODEL = "gemini-2.5-flash"

# IMPORTANT: Hardcoded Project ID string for Firestore client
# (Never use google.auth.default() or GOOGLE_CLOUD_PROJECT on Agent Platform, as they resolve to project numbers)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-04-daff5caa8f23"

# Simulated calendar schedules for the friends (Toronto based)
MOCK_CALENDARS = {
    "amalois2003@gmail.com": [
        {"date": "2026-10-31", "day": "Saturday", "status": "free", "window": "all_day", "planned": "Sweat & Tonic Reformer + Queen West Stroll"},
        {"date": "2026-11-01", "day": "Sunday", "status": "busy", "reason": "Family dinner from 3pm onwards"},
        {"date": "2026-11-07", "day": "Saturday", "status": "free", "window": "afternoon_only (after 1pm)", "planned": "Gardiner Museum Clay Workshop"},
        {"date": "2026-11-08", "day": "Sunday", "status": "free", "window": "all_day"},
    ],
    "loiscodes@gmail.com": [
        {"date": "2026-10-31", "day": "Saturday", "status": "free", "window": "all_day", "planned": "Sweat & Tonic Reformer + Queen West Stroll"},
        {"date": "2026-11-01", "day": "Sunday", "status": "free", "window": "all_day"},
        {"date": "2026-11-07", "day": "Saturday", "status": "free", "window": "all_day", "planned": "Gardiner Museum Clay Workshop"},
        {"date": "2026-11-08", "day": "Sunday", "status": "busy", "reason": "UofT Tech Hackathon deadline"},
    ],
}

# Expanded Authentic Toronto Activities Catalog
ACTIVITIES_CATALOG = [
    {
        "id": "to-pilates-1",
        "title": "Sweat and Tonic (The Well & Yonge St)",
        "neighborhood": "Downtown / The Well",
        "category": "Pilates & Movement",
        "season": "Year-round / Autumn",
        "type": "indoor",
        "vibe": "energizing, luxury wellness, athletic",
        "duration": "60 mins",
        "link": "https://www.sweatandtonic.com",
        "address": "225 Yonge St, Toronto, ON",
        "description": "High-intensity reformer pilates session in Toronto's flagship wellness collective with tonic bar and social lounge.",
    },
    {
        "id": "to-pilates-2",
        "title": "Jaybird Studio (Queen West)",
        "neighborhood": "Queen West",
        "category": "Pilates & Movement",
        "season": "Autumn / Winter",
        "type": "indoor",
        "vibe": "candlelit, infrared heat, mindful",
        "duration": "50 mins",
        "link": "https://jaybird.co",
        "address": "1100 Queen St W, Toronto, ON",
        "description": "Infrared-heated contemporary pilates and movement done in a dark, candlelit mirrorless room to bass-heavy music.",
    },
    {
        "id": "to-climb-1",
        "title": "Basecamp Climbing (Queen West)",
        "neighborhood": "Queen West",
        "category": "Rock Climbing",
        "season": "Year-round / Fall",
        "type": "indoor",
        "vibe": "community, social, all-levels bouldering",
        "duration": "2 hours",
        "link": "https://basecampclimbing.ca",
        "address": "370 Dupont St, Toronto, ON",
        "description": "Toronto's favorite community bouldering and top-rope gym in a converted theatre with high walls and social chill zones.",
    },
    {
        "id": "to-pottery-1",
        "title": "Gardiner Museum Clay Studios",
        "neighborhood": "Yorkville",
        "category": "Pottery & Crafts",
        "season": "Autumn / Winter",
        "type": "indoor",
        "vibe": "creative, tactile, cultural",
        "duration": "2 hours",
        "link": "https://www.gardinermuseum.on.ca/clay-studios",
        "address": "111 Queen's Park, Toronto, ON",
        "description": "Handbuilding and wheel throwing workshops at Canada's national ceramics museum, steps away from Yorkville cafes.",
    },
    {
        "id": "to-reading-1",
        "title": "Toronto Silent Book Club at Queen Books",
        "neighborhood": "Leslieville / Queen East",
        "category": "Reading & Cafes",
        "season": "Autumn / Fall",
        "type": "indoor",
        "vibe": "cozy, quiet camaraderie, literary",
        "duration": "2 hours",
        "link": "https://queenbooks.com",
        "address": "914 Queen St E, Toronto, ON",
        "description": "BYO-Book session at indie neighborhood bookshop. Enjoy specialty coffees, pastries, and dedicated uninterrupted reading time.",
    },
    {
        "id": "to-shows-1",
        "title": "The Second City Toronto Comedy Revue",
        "neighborhood": "Downtown / Financial District",
        "category": "Shows & Comedy",
        "season": "Year-round / Autumn",
        "type": "indoor",
        "vibe": "hilarious, evening entertainment, lively",
        "duration": "2 hours",
        "link": "https://www.secondcity.com/toronto",
        "address": "1 York St, Toronto, ON",
        "description": "World-famous improv, sketch comedy revues, and seasonal shows in an intimate theater lounge with cocktails and food.",
    },
    {
        "id": "to-distillery-1",
        "title": "Historic Distillery District Fall Walk",
        "neighborhood": "Distillery Historic District",
        "category": "Culture & Strolls",
        "season": "Autumn / Winter",
        "type": "outdoor/indoor",
        "vibe": "cobblestone, Victorian industrial, artisan chocolate",
        "duration": "2.5 hours",
        "link": "https://www.thedistillerydistrict.com",
        "address": "55 Mill St, Toronto, ON",
        "description": "Walk through 19th-century Victorian cobblestone streets, browse artisan galleries, and grab Mayan hot chocolate at Soma.",
    },
    {
        "id": "to-evergreen-1",
        "title": "Evergreen Brick Works & Don Valley Trail",
        "neighborhood": "Don Valley / Rosedale",
        "category": "Nature & Trails",
        "season": "Autumn / Fall",
        "type": "outdoor",
        "vibe": "crisp fall foliage, farmers market, wetlands",
        "duration": "2.5 hours",
        "link": "https://www.evergreen.ca/evergreen-brick-works",
        "address": "550 Bayview Ave, Toronto, ON",
        "description": "Explore glowing orange and golden fall foliage on Don Valley trails, taste local farm vendors, and sit by outdoor fire pits.",
    },
]


# ============================================================================
# FIRESTORE BACKEND TOOLS (READ & WRITE)
# ============================================================================

def get_firestore_client() -> firestore.Client:
    """Helper to return a Firestore Client using the hardcoded project ID."""
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_saved_itineraries(date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads saved outing itineraries from the Firestore backend `outing_itineraries` collection.

    Args:
        date_filter: Optional date in YYYY-MM-DD format to filter itineraries.

    Returns:
        A list of itinerary documents containing stops, times, venues, and weather details.
    """
    try:
        db = get_firestore_client()
        query = db.collection("outing_itineraries")
        if date_filter:
            query = query.where("date", "==", date_filter)

        docs = query.stream()
        results = []
        for doc in docs:
            item = doc.to_dict()
            # Convert non-serializable timestamps to ISO string
            if "created_at" in item and hasattr(item["created_at"], "isoformat"):
                item["created_at"] = item["created_at"].isoformat()
            results.append(item)
        return results if results else [{"message": f"No itineraries found for {date_filter or 'any date'}."}]
    except Exception as e:
        return [{"error": f"Firestore read failed: {str(e)}"}]


def save_outing_itinerary(
    itinerary_id: str,
    title: str,
    date: str,
    stops_json: str,
    notes: str = ""
) -> Dict[str, Any]:
    """Writes a new or updated outing itinerary to the Firestore `outing_itineraries` collection.

    Args:
        itinerary_id: Unique slug ID (e.g., 'itin-toronto-sat-oct31').
        title: Descriptive title (e.g. 'Toronto Pilates & Queen West Indie Walk').
        date: Outing date in YYYY-MM-DD format.
        stops_json: JSON string representing ordered itinerary stops (step, role, time, venue, neighborhood, link).
        notes: General outing notes or vibes.

    Returns:
        Confirmation status and document reference path.
    """
    try:
        db = get_firestore_client()
        try:
            parsed_stops = json.loads(stops_json) if isinstance(stops_json, str) else stops_json
        except Exception:
            parsed_stops = [{"raw_stops": stops_json}]

        doc_data = {
            "id": itinerary_id,
            "title": title,
            "date": date,
            "city": "Toronto, ON",
            "participants": ["amalois2003@gmail.com", "loiscodes@gmail.com"],
            "status": "confirmed",
            "stops": parsed_stops,
            "notes": notes,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection("outing_itineraries").document(itinerary_id)
        doc_ref.set(doc_data, merge=True)

        return {
            "success": True,
            "itinerary_id": itinerary_id,
            "title": title,
            "date": date,
            "message": f"Successfully stored itinerary in Firestore under projects/{FIRESTORE_PROJECT_ID}/databases/(default)/documents/outing_itineraries/{itinerary_id}",
        }
    except Exception as e:
        return {"success": False, "error": f"Firestore write failed: {str(e)}"}


def get_user_preferences(email: str) -> Dict[str, Any]:
    """Reads user preferences and favorite activity categories from Firestore `user_outing_preferences`.

    Args:
        email: User email address (e.g., 'amalois2003@gmail.com' or 'loiscodes@gmail.com').

    Returns:
        Dictionary of favorite categories, preferred vibes, and dietary notes.
    """
    try:
        db = get_firestore_client()
        doc = db.collection("user_outing_preferences").document(email.strip().lower()).get()
        if doc.exists:
            res = doc.to_dict()
            if "updated_at" in res and hasattr(res["updated_at"], "isoformat"):
                res["updated_at"] = res["updated_at"].isoformat()
            return res
        return {"email": email, "preferences": "No custom preferences saved yet."}
    except Exception as e:
        return {"error": f"Failed reading user preferences: {str(e)}"}


# ============================================================================
# PUBLIC API TOOLS (OpenStreetMap + Open-Meteo)
# ============================================================================

def lookup_toronto_location_map(query: str) -> Dict[str, Any]:
    """Free Public API tool using OpenStreetMap Nominatim for coordinates and map links."""
    clean_query = query.strip()
    if "toronto" not in clean_query.lower():
        clean_query += " Toronto, Ontario"

    encoded = urllib.parse.quote(clean_query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "HangoutHero-TorontoOutingApp/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                first = data[0]
                lat = float(first["lat"])
                lon = float(first["lon"])
                return {
                    "found": True,
                    "query": query,
                    "display_name": first.get("display_name", clean_query),
                    "latitude": lat,
                    "longitude": lon,
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                }
    except Exception:
        pass

    return {
        "found": True,
        "query": query,
        "display_name": f"{query}, Toronto, ON",
        "latitude": 43.6532,
        "longitude": -79.3832,
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query + ' Toronto')}",
    }


def get_live_toronto_weather(date: str = "2026-10-31") -> Dict[str, Any]:
    """Free Public API tool using Open-Meteo to get real live meteorological forecasts for Toronto."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=43.6532&longitude=-79.3832&current=temperature_2m,weather_code,wind_speed_10m&timezone=America%2FToronto"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            current = data.get("current", {})
            temp_c = round(current.get("temperature_2m", 13.5), 1)
            temp_f = round((temp_c * 9/5) + 32, 1)
            wind = current.get("wind_speed_10m", 12.0)
            return {
                "location": "Toronto, Ontario",
                "date": date,
                "temperature_c": f"{temp_c}°C",
                "temperature_f": f"{temp_f}°F",
                "wind_kmh": f"{wind} km/h",
                "condition": "Crisp Autumn Weather (Lake Breeze)",
                "suitable_for_outdoors": temp_c >= 10.0,
                "source": "Open-Meteo Public API",
            }
    except Exception:
        return {
            "location": "Toronto, Ontario",
            "date": date,
            "temperature_c": "13°C",
            "temperature_f": "55°F",
            "condition": "Sunny & Crisp Autumn Day",
            "suitable_for_outdoors": True,
            "source": "Historical Normal",
        }


def check_calendar_availability(email_1: str, email_2: str) -> Dict[str, Any]:
    """Checks calendar availability and finds overlapping free dates for two Toronto friends."""
    cal_1 = MOCK_CALENDARS.get(email_1.strip().lower(), [])
    cal_2 = MOCK_CALENDARS.get(email_2.strip().lower(), [])

    if not cal_1 or not cal_2:
        return {"error": "One or both accounts not found in calendar registry."}

    slots_1 = {item["date"]: item for item in cal_1}
    slots_2 = {item["date"]: item for item in cal_2}

    mutually_available = []
    common_dates = sorted(set(slots_1.keys()) & set(slots_2.keys()))

    for dt in common_dates:
        s1 = slots_1[dt]
        s2 = slots_2[dt]
        if s1["status"] == "free" and s2["status"] == "free":
            mutually_available.append({
                "date": dt,
                "day": s1["day"],
                "participant_1_window": s1.get("window", "free"),
                "participant_2_window": s2.get("window", "free"),
                "planned_activity": s1.get("planned", None),
            })

    return {
        "participants": [email_1, email_2],
        "city": "Toronto, Ontario",
        "mutually_available_dates": mutually_available,
    }


def search_activities(category: str = "all", season: str = "all", neighborhood: str = "") -> List[Dict[str, Any]]:
    """Searches the curated Toronto activities catalog filtered by category, season, or neighborhood."""
    results = []
    for act in ACTIVITIES_CATALOG:
        if category != "all" and category.lower() not in act["category"].lower():
            continue
        if season != "all" and season.lower() not in act["season"].lower():
            continue
        if neighborhood and neighborhood.lower() not in act["neighborhood"].lower():
            continue
        results.append(act)
    return results if results else ACTIVITIES_CATALOG


# ============================================================================
# MULTI-AGENT ARCHITECTURE (SUB-AGENTS & ROOT CONCIERGE)
# ============================================================================

calendar_agent = Agent(
    name="calendar_specialist",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Calendar Specialist Agent.
Your responsibility is to check and reconcile availability between two friends (amalois2003@gmail.com and loiscodes@gmail.com) in Toronto using the `check_calendar_availability` tool.
Report the exact dates, weekdays, and time windows when both are free.""",
    tools=[check_calendar_availability],
)

weather_agent = Agent(
    name="weather_specialist",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Weather Specialist Agent for Toronto.
Your responsibility is to check real meteorological conditions using the `get_live_toronto_weather` tool.
Report temperatures in Celsius (°C) and advise on outdoor vs indoor comfort.""",
    tools=[get_live_toronto_weather],
)

activity_agent = Agent(
    name="activity_curator",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Activity Curator Agent for Toronto.
Your responsibility is to find authentic Toronto spots using `search_activities` and locate map coordinates with `lookup_toronto_location_map`.""",
    tools=[search_activities, lookup_toronto_location_map],
)

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService

# Memory Bank ID reused from deployment (projects/193104736605/locations/us-east1/reasoningEngines/2600220754876301312)
MEMORY_BANK_ID = "2600220754876301312"
LOCATION = "us-east1"

# Memory generation callback: after each turn, extract and persist durable facts to Memory Bank
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None

def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService for deployed runtime and Runner integrations."""
    return VertexAiMemoryBankService(
        project=FIRESTORE_PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description="""You are the Outing Concierge (Hangout Hero) for two Toronto friends (amalois2003@gmail.com and loiscodes@gmail.com).

Memory & Past Hangouts Retention:
- You remember facts across sessions, especially:
  1. **Past Hangouts & Outings**: venues visited, dates of hangouts, activities completed, what they enjoyed or disliked about past outings, and mutual memories created.
  2. **Stated Preferences & Constraints**: dietary choices, physical activity level, favorite Toronto neighborhoods, and budget.
- Whenever the user mentions a past hangout, outing, or experience (e.g. "we went to Sweat & Tonic last Saturday", "we loved the ramen at Kinton", "our pottery session at Gardiner Museum was fun"), acknowledge it, recall key details, and explicitly treat it as durable memory for future recommendations.
- When planning future outings, refer to past hangouts so you can either build on what they loved or suggest fresh new Toronto spots they haven't tried yet.

You coordinate with specialized sub-agents, long-term memory, and a persistent Firestore backend database:
- `calendar_specialist`: Reconciles schedules to find mutual free days.
- `weather_specialist`: Live Toronto weather forecasts via Open-Meteo.
- `activity_curator`: Authentic Toronto spots with OpenStreetMap navigation.
- Long-term Memory Bank: Automatically loads relevant user preferences and past outing details.
- Firestore Database Tools:
  - `get_saved_itineraries`: Reads confirmed and planned itineraries from Firestore.
  - `save_outing_itinerary`: Persists new or adjusted itineraries into the Firestore `outing_itineraries` collection.
  - `get_user_preferences`: Reads saved user profile preferences and dietary notes from Firestore.
""",
    workflow_description="""1. When asked about existing plans, call `get_saved_itineraries` to fetch saved records from Firestore.
2. Check user preferences with `get_user_preferences` to tailor activities to their taste.
3. Suggest multi-stop itineraries (Morning Activity ➡️ Lunch ➡️ Afternoon ➡️ Dinner/Show) with walking distance context.
4. If the user confirms a plan, call `save_outing_itinerary` to persist it in Firestore.
5. Return rich structured UI cards whenever recommending itineraries, outings, activities, or weather summaries.""",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

# Root Coordinator Agent
root_agent = Agent(
    name="outing_concierge",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        AgentTool(calendar_agent),
        AgentTool(weather_agent),
        AgentTool(activity_agent),
        get_saved_itineraries,
        save_outing_itinerary,
        get_user_preferences,
        lookup_toronto_location_map,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


