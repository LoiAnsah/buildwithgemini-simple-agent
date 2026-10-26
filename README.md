# Hangout Hero · Outing Concierge 🏙️✨

An autonomous multi-agent concierge built with Google's **Agent Development Kit (ADK)** that coordinates calendars, live meteorological conditions, and authentic venues to plan, optimize, and persist outings for friends in Toronto.

![Hangout Hero Demo](docs/demo.gif)

---

## What the Agent Actually Does

Hangout Hero is orchestrated as a hierarchical multi-agent team coordinated by a central root concierge (`outing_concierge`) powered by **Gemini 2.5 Flash** on Vertex AI.

### Implemented Services & Capabilities

* **Long-Term Memory (Vertex AI Memory Bank)**:
  * Uses `PreloadMemoryTool` and an automated post-turn callback (`generate_memories_callback` invoking `add_session_to_memory`) wired to a managed **Vertex AI Memory Bank** (`agentengine://2600220754876301312`).
  * Persists durable facts across sessions: friend preferences, dietary constraints, favorite Toronto neighborhoods, and history of past hangouts.

* **Database Persistence (Google Cloud Firestore)**:
  * `get_saved_itineraries`: Queries the Firestore collection `outing_itineraries` with optional date filters to retrieve confirmed plans.
  * `save_outing_itinerary`: Persists new or adjusted multi-stop itineraries (titles, stops, dates, notes, and participant emails) into Firestore.
  * `get_user_preferences`: Reads saved user profiles and preferences from the `user_outing_preferences` collection.

* **A2UI Rich Surfaces (v0.8 Basic Catalog)**:
  * Uses `A2uiSchemaManager` (version 0.8) and `BasicCatalog` to emit structured `beginRendering` and `surfaceUpdate` JSON payloads.
  * Paired with `a2ui_callback` (`after_model_callback`) to wrap UI component arrays in `<a2a_datapart_json>` envelopes for native rendering in ADK Web and the custom web frontend.

* **Multi-Agent Delegation**:
  * `calendar_specialist`: Inspects schedules and calculates mutual overlapping free windows for friend pairs.
  * `weather_specialist`: Connects to the **Open-Meteo** API to fetch real-time Toronto weather forecasts (temperature in °C, wind speed, precipitation conditions) to determine indoor vs. outdoor feasibility.
  * `activity_curator`: Explores an authentic curated Toronto activities catalog (pilates, climbing, pottery, indie bookstores, and bistros) and calculates coordinates using **OpenStreetMap Nominatim**.

---

## Planned / Roadmap Features

The following features were outlined in the original design brief but are **planned, not yet implemented**:
* **Image Generation & Cloud Storage**: Generating stylized shareable outing invitation cards via Imagen and saving them to Google Cloud Storage.
* **Code Sandbox / Dynamic Compute**: Executing code in a container sandbox for fine-grained budget and bill splitting.
* **Live Google Calendar OAuth**: Direct OAuth synchronization with live Google Calendar accounts (currently runs via simulated calendar registry).

---

## Architecture & Project Structure

```text
simple-agent/
├── app/
│   ├── agent.py               # Root concierge, sub-agents, Memory Bank service, and Firestore tools
│   ├── a2ui_utils.py          # A2UI response formatting callback for v0.8 components
│   └── fast_api_app.py        # Local ASGI app wrapper
├── frontend/
│   ├── main.py                # FastAPI proxy communicating over A2A protocol
│   ├── requirements.txt       # Frontend dependencies
│   └── static/
│       └── index.html         # Web chat interface with embedded A2UI card renderer
├── docs/
│   └── demo.gif               # Looping demonstration recording
├── agents-cli-manifest.yaml   # ADK / Agent Runtime deployment metadata
└── pyproject.toml             # Python environment and package specifications
```

---

## Running Locally

### Prerequisites
* Python 3.10+
* `uv` package manager
* Google Cloud SDK (`gcloud`) authenticated with a project having Vertex AI and Firestore permissions

### 1. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Launch the ADK Web Playground with Memory Bank
Run the local ADK developer playground pointing at your Vertex AI Memory Bank:
```bash
cd simple-agent
GOOGLE_CLOUD_LOCATION=us-east1 uv run --frozen adk web . \
  --port 8080 \
  --reload_agents \
  --memory_service_uri=agentengine://YOUR_MEMORY_BANK_ID
```
*(In the ADK Dev UI settings, ensure Token Streaming is disabled to view rich A2UI cards).*

### 3. Run the Custom A2A Chat Frontend
To run the lightweight chat UI proxy locally against a deployed Agent Runtime:
```bash
cd simple-agent/frontend
pip install -r requirements.txt

export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_NUM/locations/us-east1/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"

python main.py
```
