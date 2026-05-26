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
    get_lineup_tool,
    get_player_stats_tool,
    recommend_lineup_tool,
    suggest_transfer_tool,
    recommend_captain_tool,
    compare_players_tool,
    get_form_analysis_tool,
)

from tools.prediction_engine import (
    get_team_stats_tool,
    predict_match_tool,
    get_tournament_standings_tool,
    get_live_2026_standings_tool,
    get_live_2026_top_scorers_tool
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

        You have access to the following tools and MUST use them to answer questions:
        - get_players: retrieve players filtered by position
        - get_player_stats: get aggregated fantasy points, goals, assists per player
        - get_top_scorers: get players with most goals
        - get_matches: get match fixtures and results
        - get_matchdays: get tournament rounds
        - recommend_lineup: generate optimal 11 player lineup
        - save_lineup: save a lineup for a user
        - get_lineup: retrieve a saved lineup
        - suggest_transfer: analyze lineup and recommend best transfer in/out
        - recommend_captain: pick best captain from current lineup
        - compare_players: head to head comparison of two players
        - get_form_analysis: rank players by recent weighted performance
        - get_team_stats: analyze a team's attack, defense, and win rate
        - predict_match: predict outcome between two teams with probabilities
        - get_tournament_standings: get overall tournament table
        - get_live_2026_standings: get current 2026 World Cup group standings
        - get_live_2026_top_scorers: get current 2026 World Cup top scorers

        CRITICAL RULES:
        1. ALWAYS call the appropriate tool before answering any question about players, 
        stats, or lineups. Never answer from memory alone.
        2. When asked about top performers or fantasy points, use get_player_stats tool.
        3. When asked to recommend a lineup, use recommend_lineup tool first, then 
        save_lineup to persist it.
        4. When saving a lineup, use the recommended players from recommend_lineup as 
        starters and bench. Do not ask the user to provide player names.
        5. Position requirements are strict: exactly 1 GK, 4 DEF, 3 MID, 3 FWD.
        6. Always explain your reasoning clearly after every tool call.
        7. When asked to do multiple things, do all of them in sequence.

        Scoring system for context:
        - Playing 60+ minutes: 2 points
        - Playing 1-59 minutes: 1 point  
        - Goal (FWD): 4 points
        - Goal (MID): 5 points
        - Goal (DEF/GK): 6 points
        - Assist: 3 points
        - Clean sheet (GK/DEF): 4 points
        - Clean sheet (MID): 1 point
        - Every 3 saves (GK): 1 point
        - Yellow card: -1 point
        - Red card: -3 points
        - Own goal: -2 points
        """,
        tools=[
            get_players_tool,
            get_top_scorers_tool,
            get_matches_tool,
            get_matchdays_tool,
            save_lineup_tool,
            get_lineup_tool,
            get_player_stats_tool,
            recommend_lineup_tool,
            suggest_transfer_tool,
            recommend_captain_tool,
            compare_players_tool,
            get_form_analysis_tool,
            get_team_stats_tool,
            predict_match_tool,
            get_tournament_standings_tool,
            get_live_2026_standings_tool,
            get_live_2026_top_scorers_tool,
        ]
    )
    return agent

root_agent = create_agent()