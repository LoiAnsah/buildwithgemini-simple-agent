"""FastAPI proxy for Hangout Hero connecting to deployed Agent Runtime over A2A protocol.

Features:
- Serves rich interactive UI: Interactive Leaflet Map, Mutual Calendar Matrix, Activities Catalog.
- Proxies /chat and /api/chat over A2A protocol with native A2UI payload support.
- Local endpoints for mock activities catalog and calendar schedule data.
"""

import os
import sys
import uuid
from pathlib import Path

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    FilePart,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TextPart,
    TransportProtocol,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Hardcoded catalog and calendar data for frontend widgets
ACTIVITIES_CATALOG = [
    {
        "id": "to-pilates-1",
        "title": "Sweat and Tonic (The Well)",
        "neighborhood": "Downtown / The Well",
        "category": "Pilates & Movement",
        "season": "Year-round",
        "type": "indoor",
        "vibe": "energizing, luxury wellness, athletic",
        "duration": "60 mins",
        "link": "https://www.sweatandtonic.com",
        "address": "225 Yonge St, Toronto, ON",
        "description": "High-intensity reformer pilates session in Toronto's flagship wellness collective.",
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
        "description": "Infrared-heated contemporary pilates and movement in a dark candlelit room.",
    },
    {
        "id": "to-climb-1",
        "title": "Basecamp Climbing (Queen West)",
        "neighborhood": "Queen West",
        "category": "Rock Climbing",
        "season": "Year-round",
        "type": "indoor",
        "vibe": "community, social, bouldering",
        "duration": "2 hours",
        "link": "https://basecampclimbing.ca",
        "address": "370 Dupont St, Toronto, ON",
        "description": "Toronto's favorite community bouldering and top-rope climbing gym.",
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
        "description": "Handbuilding and wheel throwing workshops at Canada's national ceramics museum.",
    },
    {
        "id": "to-reading-1",
        "title": "Toronto Silent Book Club at Queen Books",
        "neighborhood": "Leslieville",
        "category": "Reading & Cafes",
        "season": "Autumn",
        "type": "indoor",
        "vibe": "cozy, quiet camaraderie, literary",
        "duration": "2 hours",
        "link": "https://queenbooks.com",
        "address": "914 Queen St E, Toronto, ON",
        "description": "BYO-Book session at indie neighborhood bookshop with specialty coffee.",
    },
    {
        "id": "to-distillery-1",
        "title": "Historic Distillery District Fall Walk",
        "neighborhood": "Distillery Historic District",
        "category": "Culture & Strolls",
        "season": "Autumn",
        "type": "outdoor/indoor",
        "vibe": "cobblestone, Victorian industrial, artisan hot chocolate",
        "duration": "2.5 hours",
        "link": "https://www.thedistillerydistrict.com",
        "address": "55 Mill St, Toronto, ON",
        "description": "Walk through 19th-century Victorian cobblestone streets and artisan chocolate at Soma.",
    },
]

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

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/193104736605/locations/us-east1/reasoningEngines/2600220754876301312"
)
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"
_A2UI_MIME = "application/json+a2ui"

_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }

app = FastAPI(title="Hangout Hero Outing Proxy")

@app.get("/api/activities")
async def get_activities():
    return {"activities": ACTIVITIES_CATALOG}

@app.get("/api/calendar")
async def get_calendar():
    return {"calendars": MOCK_CALENDARS}

@app.get("/api/itineraries")
async def get_itineraries():
    return {"itineraries": []}

_contexts: dict[str, str] = {}
_card: AgentCard | None = None

async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        card = AgentCard(**resp.json())
        card.url = A2A_BASE
        _card = card
    return _card

def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        if isinstance(root, TextPart) and getattr(root, "text", None):
            out.append({"kind": "text", "text": root.text})
        elif getattr(root, "data", None) is not None:
            meta = getattr(root, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": root.data})
        elif isinstance(root, FilePart):
            uri = getattr(getattr(root, "file", None), "uri", None)
            if uri:
                out.append({"kind": "text", "text": uri})
    return out

@app.post("/chat")
@app.post("/api/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
            card = await _get_card(client)
            factory = ClientFactory(
                ClientConfig(
                    supported_transports=[
                        TransportProtocol.jsonrpc,
                        TransportProtocol.http_json,
                    ],
                    httpx_client=client,
                )
            )
            a2a_client = factory.create(card)

            msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(text=message))],
                context_id=_contexts.get(user_id),
            )

            last_task = None
            got_artifact_update = False
            async for event in a2a_client.send_message(msg):
                if not isinstance(event, tuple):
                    continue
                task, update = event
                if task is not None:
                    last_task = task
                    if getattr(task, "context_id", None):
                        _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    got_artifact_update = True
                    parts.extend(_extract_parts(update.artifact.parts))

            if not got_artifact_update and last_task is not None:
                for artifact in getattr(last_task, "artifacts", None) or []:
                    parts.extend(_extract_parts(artifact.parts))

        if not parts:
            parts = [{"kind": "text", "text": "(The agent processed your request.)"}]

        # reply string for legacy chat callers
        text_replies = [p["text"] for p in parts if p.get("kind") == "text" and p.get("text")]
        reply_str = "\n\n".join(text_replies) if text_replies else "(Response received)"

        return JSONResponse({"reply": reply_str, "parts": parts})
    except Exception as exc:
        err = f"Error: {type(exc).__name__}: {exc}"
        return JSONResponse({"reply": err, "parts": [{"kind": "text", "text": err}]})

# Serve static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
