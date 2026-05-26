import os
from dotenv import load_dotenv

import json
import tempfile

load_dotenv()

credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if credentials_json:
    try:
        creds_dict = json.loads(credentials_json)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(creds_dict, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
    except Exception as e:
        print(f"Failed to load credentials: {e}")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", "fluid-booking-496802-d8")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from agent.agent import root_agent

app = FastAPI(title="Pitchside API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

runner = InMemoryRunner(
    agent=root_agent,
    app_name="pitchside"
)

sessions = {}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "pitchside"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id

    if user_id not in sessions:
        session = await runner.session_service.create_session(
            app_name="pitchside",
            user_id=user_id
        )
        sessions[user_id] = session.id

    session_id = sessions[user_id]

    message = Content(
        role="user",
        parts=[Part(text=request.message)]
    )

    response_text = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

    # check if a lineup was saved during this interaction
    from database.schema import get_database
    db = get_database()
    latest_lineup = db.lineups.find_one(
        {"user_id": user_id},
        {"_id": 0},
        sort=[("matchday", -1)]
    )

    return ChatResponse(
       content={
            "response": response_text or "I couldn't process that request.",
            "session_id": session_id,
            "lineup": latest_lineup
       },
       headers={"Access-Control-Allow-Origin": "*"}
    )

@app.get("/lineup/{user_id}")
async def get_lineup(user_id: str, matchday: int = 1):
    from database.schema import get_database
    db = get_database()
    lineup = db.lineups.find_one(
        {"user_id": user_id, "matchday": matchday},
        {"_id": 0}
    )
    return {"lineup": lineup}

@app.get("/standings")
async def get_standings():
    from tools.prediction_engine import get_tournament_standings
    return get_tournament_standings()

@app.get("/top-performers")
async def get_top_performers(limit: int = 10):
    from tools.mongodb_tools import get_player_stats
    return get_player_stats(limit=limit)

@app.get("/players")
async def get_players(position: str = None, limit: int = 60):
    from database.schema import get_database
    db = get_database()
    query = {}
    if position:
        query["position"] = position
    players = list(db.players.find(query, {
       "_id": 0,
        "api_id": 1,
        "name": 1,
        "nationality": 1,
        "position": 1,
        "photo": 1,
        "club": 1
    }).limit(limit))
    return {"playeres": players}