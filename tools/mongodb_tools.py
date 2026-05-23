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

def suggest_transfer(user_id: str, matchday: int) -> dict:
    """Analyze current lineup and suggest the best transfer to improve it. 
    
    Args:
        user_id: The user's identifier.
        matchday: The current matchday number.

    Returns:
        Dictionary with transfer suggestion and reasoning
    """
    db = get_db()

    lineup = db.lineups.find_one({"user_id": user_id, "matchday": matchday})
    if not lineup:
        return {"status": "error", "message": "No lineup found. Please get a recommendation first."}

    current_starters = lineup.get("starters", [])

    starter_stats = []
    for player in current_starters:
        name = player if isinstance(player, str) else player.get("name", "")
        pipeline = [
            {"$match": {"player_name": {"$regex": name, "$options": "i"}}},
            {"$group": {
                "_id": "$player_name",
                "total_points": {"$sum": "$fantasy_points"},
                "goals": {"$sum": "$goals"},
                "assists": {"$sum": "$assists"},
                "matches": {"$sum": 1},
                "yellow_cards": {"$sum": "$yellow_cards"},
                "red_cards": {"$sum": "$red_cards"}
            }}
        ]
        result = list(db.player_stats.aggregate(pipeline))
        if result:
            starter_stats.append(result[0])
        
    if not starter_stats:
        return {"status": "error", "message": "Could not retrieve stats for current lineup."}

    starter_stats.sort(key=lambda x: x["total_points"])
    weakest = starter_stats[0]
    weakest_name = weakest["_id"]

    weakest_player = db.players.find_one(
        {"name": {"$regex": weakest_name, "$options": "i"}},
        {"position": 1}
    )
    position = weakest_player["position"] if weakest_player else "MID"

    current_names = [
        p if isinstance(p, str) else p.get("name", "")
        for p in current_starters
    ]

    pipeline = [
        {"$match": {"player_name": {"$nin": current_names}}},
        {"$group": {
            "_id": "$api_player_id",
            "player_name": {"$first": "$player_name"},
            "total_points": {"$sum": "$fantasy_points"},
            "goals": {"$sum": "$goals"},
            "assists": {"$sum": "$assists"},
            "matches": {"$sum": 1}
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": 20}
    ]

    candidates = list(db.player_stats.aggregate(pipeline))

    best_replacement = None
    for candidate in candidates:
        player = db.players.find_one(
            {"api_id": candidate["_id"]},
            {"position": 1, "name": 1}
        )
        if player and player.get("position") == position:
            best_replacement = candidate
            break
    
    if not best_replacement:
        best_replacement = candidates[0] if candidates else None

    return{
        "transfer_out": {
            "name": weakest_name,
            "position": position,
            "total_points": weakest["total_points"],
            "reason": "Lowest fantasy points in current lineup"
        },
        "transfer_in": {
            "name": best_replacement["player_name"] if best_replacement else "No candidate found",
            "total_points": best_replacement["total_points"] if best_replacement else 0,
            "goals": best_replacement["goals"] if best_replacement else 0,
            "assists": best_replacement["assists"] if best_replacement else 0
        },
        "points_gain": (best_replacement["total_points"] if best_replacement else 0) - weakest["total_points"]
    }

def recommend_captain(user_id: str, matchday: int) -> dict:
    """Recommend the best captain from the user's current lineup.
    
    Args:
        user_id: The user's identifier.
        matchday: The current matchday number.

    Returns:
        Dictionary with captain recommendation and reasoning.
    """

    db = get_db()

    lineup = db.lineups.find_one({"user_id": user_id, "matchday": matchday})
    if not lineup:
        return {"status": "error", "message": "No lineup found for this matchday."}
    
    current_starters = lineup.get("starters", [])
    player_performances = []

    for player in current_starters:
        name = player if isinstance(player, str) else player.get("name", "")
        pipeline = [
            {"$match": {"player_name": {"$regex": name, "$options": "i"}}},
            {"$group": {
                "_id": "$player_name",
                "total_points": {"$sum": "$fantasy_points"},
                "goals": {"$sum": "$goals"},
                "assists": {"$sum": "$assists"},
                "matches": {"$sum": 1},
                "avg_points": {"$avg": "$fantasy_points"}
            }}
        ]
        result = list(db.player_stats.aggregate(pipeline))
        if result:
            player_performances.append(result[0])

    if not player_performances:
        return {"status": "error", "message": "Could not retrieve stats for lineup."}

    player_performances.sort(key=lambda x: x["total_points"], reverse=True)
    captain = player_performances[0]
    vice_captain = player_performances[1] if len(player_performances) > 1 else None

    return {
        "captain": {
            "name": captain["_id"],
            "total_points": captain["total_points"],
            "goals": captain["goals"],
            "assists": captain["assists"],
            "avg_points_per_match": round(captain["avg_points"], 2),
            "captain_bonus": f"Expected doubled points: ~{captain['total_points'] * 2}"
        },
        "vice_captain": {
            "name": vice_captain["_id"] if vice_captain else None,
            "total_points": vice_captain["total_points"] if vice_captain else 0
        },
        "reasoning": f"{captain['_id']} leads your squad with {captain['total_points']} total points, {captain['goals']} goals and {captain['assists']} assists."
    }

def compare_players(player1_name: str, player2_name: str) -> dict:
    """Compare two players head to head by their tournament statistics.
    
    Args:
        player1_name: Name of the first player.
        player2_name: Name of the second player.

    Returns:
        Dictionary with side by side comparison and recommendation
    """

    db = get_db()

    def get_stats(name):
        pipeline = [
            {"$match": {"player_name": {"$regex": name, "$options": "i"}}},
            {"$group": {
                "_id": "$player_name",
                "total_points": {"$sum": "$fantasy_points"},
                "goals": {"$sum": "$goals"},
                "assists": {"$sum": "$assists"},
                "minutes": {"$sum": "$minutes_played"},
                "yellow_cards": {"$sum": "$yellow_cards"},
                "red_cards": {"$sum": "$red_cards"},
                "matches": {"$sum": 1},
                "avg_points": {"$avg": "$fantasy_points"}
            }}
        ]
        result = list(db.player_stats.aggregate(pipeline))
        return result[0] if result else None
    
    p1 = get_stats(player1_name)
    p2 = get_stats(player2_name)

    if not p1:
        return {"status": "error", "message": f"No stats found for {player1_name}"}
    if not p2:
        return {"status": "error", "message": f"No stats found for {player2_name}"}

    winner = p1["_id"] if p1["total_points"] >= p2["total_points"] else p2["_id"]
    margin = abs(p1["total_points"] - p2["total_points"])

    return {
        "player1": {
            "name": p1["_id"],
            "total_points": p1["total_points"],
            "goals": p1["goals"],
            "assists": p1["assists"],
            "matches": p1["matches"],
            "avg_points_per_match": round(p1["avg_points"], 2),
            "yellow_cards": p1["yellow_cards"],
            "red_cards": p1["red_cards"]
        },
        "player2": {
            "name": p2["_id"],
            "total_points": p2["total_points"],
            "goals": p2["goals"],
            "assists": p2["assists"],
            "matches": p2["matches"],
            "avg_points_per_match": round(p2["avg_points"], 2),
            "yellow_cards": p2["yellow_cards"],
            "red_cards": p2["red_cards"]
        },
        "recommendation": winner,
        "margin": margin,
        "verdict": f"Pick {winner} — they outscored the alternative by {margin} fantasy points."
    }

def get_form_analysis(limit: int = 10) -> dict:
    """Analyze player form by weighting recent match performances more heavily.
    
    Args:
        limit: Number of top in-form players to return. Default 10.
    
    Returns:
        Dictionary with in-form players ranked by weighted performance.
    """
    db = get_db()

    pipeline = [
        {"$sort": {"matchday": -1}},
        {"$group": {
            "_id": "$api_player_id",
            "player_name": {"$first": "$player_name"},
            "recent_points": {"$first": "$fantasy_points"},
            "total_points": {"$sum": "$fantasy_points"},
            "matches": {"$push": {
                "matchday": "$matchday",
                "points": "$fantasy_points",
                "goals": "$goals",
                "assists": "$assists"
            }},
            "match_count": {"$sum": 1}
        }},
        {"$match": {"match_count": {"$gte": 2}}},
        {"$limit": 100}
    ]

    all_players = list(db.player_stats.aggregate(pipeline))

    for player in all_players:
        matches = sorted(player["matches"], key=lambda x: x["matchday"], reverse=True)
        weights = [1.5, 1.2, 1.0, 0.8, 0.6]
        weighted_score = 0
        for i, match in enumerate(matches[:5]):
            weight = weights[i] if i < len(weights) else 0.5
            weighted_score += match["points"] * weight
        player["form_score"] = round(weighted_score, 2)
        player["last_3_matches"] = matches[:3]

    all_players.sort(key=lambda x: x["form_score"], reverse=True)
    top_form = all_players[:limit]

    return {
        "in_form_players": [
            {
                "name": p["player_name"],
                "form_score": p["form_score"],
                "total_points": p["total_points"],
                "recent_points": p["recent_points"],
                "last_3_matches": p["last_3_matches"]
            }
            for p in top_form
        ],
        "note": "Form score weights recent matches more heavily: 1.5x, 1.2x, 1.0x, 0.8x, 0.6x"
    }    


suggest_transfer_tool = FunctionTool(suggest_transfer)
recommend_captain_tool = FunctionTool(recommend_captain)
compare_players_tool = FunctionTool(compare_players)
get_form_analysis_tool = FunctionTool(get_form_analysis)

get_player_stats_tool = FunctionTool(get_player_stats)
recommend_lineup_tool = FunctionTool(recommend_lineup)

get_players_tool = FunctionTool(get_players)
get_top_scorers_tool = FunctionTool(get_top_scorers)
get_matches_tool = FunctionTool(get_matches)
get_matchdays_tool = FunctionTool(get_matchdays)
save_lineup_tool = FunctionTool(save_lineup)
get_lineup_tool = FunctionTool(get_lineup)
