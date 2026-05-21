import os
from pymongo import MongoClient
from dotenv import load_dotenv
from google.adk.tools import FunctionTool

load_dotenv()


def get_db():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["worldcup_fantasy"]


def get_players(position: str = None, limit: int = 10) -> dict:
    """Get players from the database, optionally filtered by position.

    Args:
        position: Player position (GK, DEF, MID, FWD). Optional.
        limit: Maximum number of players to return. Default 10.

    Returns:
        Dictionary with list of players and total count.
    """
    db = get_db()
    query = {}
    if position:
        query["position"] = position

    players = list(db.players.find(query, {"_id": 0}).limit(limit))
    total = db.players.count_documents(query)

    return {"players": players, "total": total, "returned": len(players)}


def get_top_scorers(limit: int = 10) -> dict:
    """Get players with the most goals from historical 2022 World Cup data.

    Args:
        limit: Maximum number of players to return. Default 10.

    Returns:
        Dictionary with list of top scoring players.
    """
    db = get_db()
    players = list(
        db.players.find(
            {"historical_2022.goals": {"$exists": True}},
            {
                "_id": 0,
                "name": 1,
                "position": 1,
                "nationality": 1,
                "historical_2022": 1,
            },
        )
        .sort("historical_2022.goals", -1)
        .limit(limit)
    )

    return {"top_scorers": players, "count": len(players)}


def get_matches(stage: str = None, status: str = None) -> dict:
    """Get World Cup matches, optionally filtered by stage or status.

    Args:
        stage: Match stage (group, round_of_16, quarter_final, semi_final, final). Optional.
        status: Match status (scheduled, live, finished). Optional.

    Returns:
        Dictionary with list of matches.
    """
    db = get_db()
    query = {}
    if stage:
        query["stage"] = stage
    if status:
        query["status"] = status

    matches = list(db.matches.find(query, {"_id": 0}).limit(20))
    total = db.matches.count_documents(query)

    return {"matches": matches, "total": total}


def get_matchdays() -> dict:
    """Get all matchdays and their status.

    Returns:
        Dictionary with list of matchdays.
    """
    db = get_db()
    matchdays = list(db.matchdays.find({}, {"_id": 0}).sort("matchday_number", 1))
    return {"matchdays": matchdays}


def save_lineup(
    user_id: str,
    matchday: int,
    starters: list,
    bench: list,
    formation: str,
    reasoning: str,
) -> dict:
    """Save a fantasy lineup for a user.

    Args:
        user_id: The user's identifier.
        matchday: The matchday number.
        starters: List of 11 starter player names.
        bench: List of 4 bench player names.
        formation: Formation string like 4-3-3.
        reasoning: Agent's reasoning for this lineup.

    Returns:
        Dictionary confirming the save.
    """
    db = get_db()

    lineup_doc = {
        "user_id": user_id,
        "matchday": matchday,
        "starters": starters,
        "bench": bench,
        "formation": formation,
        "agent_recommendation": reasoning,
        "locked": False,
    }

    db.lineups.update_one(
        {"user_id": user_id, "matchday": matchday}, {"$set": lineup_doc}, upsert=True
    )

    return {"status": "saved", "user_id": user_id, "matchday": matchday}


def get_lineup(user_id: str, matchday: int) -> dict:
    """Get a user's saved fantasy lineup for a matchday.

    Args:
        user_id: The user's identifier.
        matchday: The matchday number.

    Returns:
        Dictionary with the lineup details.
    """
    db = get_db()
    lineup = db.lineups.find_one({"user_id": user_id, "matchday": matchday}, {"_id": 0})

    if not lineup:
        return {
            "status": "not_found",
            "message": f"No lineup found for matchday {matchday}",
        }

    return {"lineup": lineup}


get_players_tool = FunctionTool(get_players)
get_top_scorers_tool = FunctionTool(get_top_scorers)
get_matches_tool = FunctionTool(get_matches)
get_matchdays_tool = FunctionTool(get_matchdays)
save_lineup_tool = FunctionTool(save_lineup)
get_lineup_tool = FunctionTool(get_lineup)
