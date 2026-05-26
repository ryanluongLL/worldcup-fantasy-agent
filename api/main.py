import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from agent.agent import root_agent

app = FastAPI(title="Pitchside API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
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

@app.post("/chat", response_model=ChatResponse)
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
    return ChatResponse(
        response=response_text or "I couldn't process that request. Please try again.",
        session_id=session_id
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