import os
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()

os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from tools.mongodb_tools import (
    get_players_tool,
    get_top_scorers_tool,
    get_matches_tool,
    get_matchdays_tool,
    save_lineup_tool,
    get_lineup_tool
)

def create_agent():
    agent = Agent(
        model="gemini-2.5-flash",
        name="worldcup_fantasy_agent",
        description="A World Cup fantasy football agent.",
        instruction="""
        You are an expert World Cup fantasy football agent with access to a MongoDB
        database containing 2022 World Cup player data, match fixtures, and historical
        statistics.

        When making recommendations:
        1. Always query the database first to get current data
        2. Consider position requirements: 1 GK, 4 DEF, 3 MID, 3 FWD
        3. Factor in goals, assists, clean sheets, cards, and minutes played
        4. Explain your reasoning clearly so users understand every decision
        5. Flag players with red cards or poor form proactively

        Always be helpful, specific, and data-driven in your recommendations.
        """,
        tools=[
            get_players_tool,
            get_top_scorers_tool,
            get_matches_tool,
            get_matchdays_tool,
            save_lineup_tool,
            get_lineup_tool
        ]
    )
    return agent

root_agent = create_agent()