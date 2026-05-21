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

def get_player_stats(player_name: str = None, limit: int = 10) -> dict:
    """Get player match statistics from the database.
    
    Args:
        player_name: Filter by player name. Optional.
        limit: Maximum number of records to return. Default 10.
    
    Returns:
        Dictionary with player stats aggregated across matches.
    """
    db = get_db()
    pipeline = []

    if player_name:
        pipeline.append({"$match": {"player_name": {"$regex": player_name, "$options": "i"}}})

    pipeline += [
        {
            "$group": {
                "_id": "$player_name",
                "total_points": {"$sum": "$fantasy_points"},
                "total_goals": {"$sum": "$goals"},
                "total_assists": {"$sum": "$assists"},
                "total_minutes": {"$sum": "$minutes_played"},
                "yellow_cards": {"$sum": "$yellow_cards"},
                "red_cards": {"$sum": "$red_cards"},
                "matches_played": {"$sum": 1}
            }
        },
        {"$sort": {"total_points": -1}},
        {"$limit": limit}
    ]

    results = list(db.player_stats.aggregate(pipeline))
    for r in results:
        r["player_name"] = r.pop("_id")

    return {"stats": results, "count": len(results)}

def recommend_lineup(user_id: str, matchday: int) -> dict:
    """Generate an optimal fantasy lineup recommendation based on player performance.
    
    Args:
        user_id: The user's identifier.
        matchday: The matchday number to recommend for.
    
    Returns:
        Dictionary with recommended starters, bench, and reasoning.
    """
    db = get_db()

    pipeline = [
        {
            "$group": {
                "_id": "$api_player_id",
                "player_name": {"$first": "$player_name"},
                "total_points": {"$sum": "$fantasy_points"},
                "total_goals": {"$sum": "$goals"},
                "total_assists": {"$sum": "$assists"},
                "matches_played": {"$sum": 1},
                "yellow_cards": {"$sum": "$yellow_cards"},
                "red_cards": {"$sum": "$red_cards"}
            }
        },
        {"$sort": {"total_points": -1}}
    ]

    all_stats = list(db.player_stats.aggregate(pipeline))

    player_ids = [s["_id"] for s in all_stats]
    players_map = {}

    for p in db.players.find({"api_id": {"$in": player_ids}}):
        players_map[p["api_id"]] = p

    by_position = {"GK": [], "DEF": [], "MID": [], "FWD": []}

    for stat in all_stats:
        player = players_map.get(stat["_id"])
        if not player:
            continue
        position = player.get("position", "MID")
        if position in by_position:
            by_position[position].append({
                "name": stat["player_name"],
                "position": position,
                "total_points": stat["total_points"],
                "goals": stat["total_goals"],
                "assists": stat["total_assists"],
                "matches": stat["matches_played"],
                "yellow_cards": stat["yellow_cards"],
                "red_cards": stat["red_cards"],
                "nationality": player.get("nationality", "Unknown")
            })

    starters = []
    bench = []

    if by_position["GK"]:
        starters.append(by_position["GK"][0])
        if len(by_position["GK"]) > 1:
            bench.append(by_position["GK"][1])

    for defender in by_position["DEF"][:4]:
        starters.append(defender)
    if len(by_position["DEF"]) > 4:
        bench.append(by_position["DEF"][4])

    for midfielder in by_position["MID"][:3]:
        starters.append(midfielder)
    if len(by_position["MID"]) > 3:
        bench.append(by_position["MID"][3])

    for forward in by_position["FWD"][:3]:
        starters.append(forward)
    if len(by_position["FWD"]) > 3:
        bench.append(by_position["FWD"][3])

    return {
        "matchday": matchday,
        "formation": "4-3-3",
        "starters": starters,
        "bench": bench,
        "total_starters": len(starters),
        "note": "Ranked by total fantasy points across all 2022 World Cup matches"
    }

get_player_stats_tool = FunctionTool(get_player_stats)
recommend_lineup_tool = FunctionTool(recommend_lineup)

get_players_tool = FunctionTool(get_players)
get_top_scorers_tool = FunctionTool(get_top_scorers)
get_matches_tool = FunctionTool(get_matches)
get_matchdays_tool = FunctionTool(get_matchdays)
save_lineup_tool = FunctionTool(save_lineup)
get_lineup_tool = FunctionTool(get_lineup)
