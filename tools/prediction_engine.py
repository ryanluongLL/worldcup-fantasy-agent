import os
from pymongo import MongoClient
from dotenv import load_dotenv
from google.adk.tools import FunctionTool

load_dotenv()

def get_db():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["worldcup_fantasy"]

def get_team_stats(team_name: str) -> dict:
    """Calculate attack and defense strength for a team based on 2022 results.
    
    Args:
        team_name: The team name to analyze.

    Returns:
        Dictionary with goals cored, conceded, win rate and form.
    """
    db = get_db()

    home_matches = list(db.matches.find(
        {"home_team": {"$regex": team_name, "$options": "i"}, "status": "finished"},
        {"score": 1, "home_team": 1, "away_team": 1, "stage": 1}
    ))

    away_matches = list(db.matches.find(
        {"away_team": {"$regex": team_name, "$options": "i"}, "status": "finished"},
        {"score": 1, "home_team": 1, "away_team": 1, "stage": 1}
    ))

    all_matches = []

    for m in home_matches:
        scored = m["score"]["home"] or 0
        conceded = m["score"]["away"] or 0
        result = "win" if scored > conceded else ("draw" if scored == conceded else "loss")
        all_matches.append({
            "opponent": m["away_team"],
            "scored": scored,
            "conceded": conceded,
            "result": result,
            "stage": m["stage"]
        })
    
    for m in away_matches:
        scored = m["score"]["away"] or 0
        conceded = m["score"]["home"] or 0
        result = "win" if scored > conceded else ("draw" if scored == conceded else "loss")
        all_matches.append({
            "opponent": m["home_team"],
            "scored": scored,
            "conceded": conceded,
            "result": result,
            "stage": m["stage"]
        })
    
    if not all_matches:
        return {"status": "error", "message": f"No matches found for {team_name}"}

    total_matches = len(all_matches)
    total_scored = sum(m["scored"] for m in all_matches)
    total_conceded = sum(m["conceded"] for m in all_matches)
    wins = sum(1 for m in all_matches if m["result"] == "win")
    draws = sum(1 for m in all_matches if m["result"] == "draw")
    losses = sum(1 for m in all_matches if m["result"] == 'loss')

    recent = sorted(all_matches, key=lambda x: ["group", "round_of_32",
        "round_of_16", "quarter_final", "semi_final", "final"].index(x["stage"])
        if x["stage"] in ["group", "round_of_32", "round_of_16",
        "quarter_final", "semi_final", "final"] else 0, reverse=True)[:3]
    
    return {
        "team": team_name,
        "matches_played": total_matches,
        "goals_scored": total_scored,
        "goals_conceded": total_conceded,
        "goals_per_game": round(total_scored / total_matches, 2),
        "conceded_per_game": round(total_conceded / total_matches, 2),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": round(wins / total_matches * 100, 1),
        "recent_form": recent,
        "all_matches": all_matches
    }

def predict_match(team1: str, team2: str) -> dict:
    """Predict the outcome of a match between two teams using historical data.
    
    Args:
        team1: Name of the first team.
        team2: Name of the second team.

    Returns:
        Dictionary with prediction, probabilities, and reasoning.
    """
    db = get_db()

    t1 = get_team_stats(team1)
    t2 = get_team_stats(team2)

    if "error" in t1.get("status", ""):
        return t1
    if "error" in t2.get("status", ""):
        return t2
    
    t1_attack = t1["goals_per_game"]
    t1_defense = t1["conceded_per_game"]
    t2_attack = t2["goals_per_game"]
    t2_defense= t2["conceded_per_game"]

    t1_strength = (t1_attack * 0.6) + ((1 / (t1_defense + 0.1)) * 0.4)
    t2_strength = (t2_attack * 0.6) + ((1 / (t2_defense + 0.1)) * 0.4)

    total = t1_strength + t2_strength
    t1_win_prob = round((t1_strength / total)* 100, 1)
    t2_win_prob = round((t2_strength / total) * 100, 1)
    draw_prob = round(max(0,30 - abs(t1_win_prob - t2_win_prob)), 1)

    t1_win_prob = round(t1_win_prob * (1 - draw_prob / 100), 1)
    t2_win_prob = round(t2_win_prob * (1 - draw_prob / 100), 1)

    if t1_win_prob > t2_win_prob:
        predicted_winner = team1          
        confidence = "High" if t1_win_prob > 60 else "Medium"
    elif t2_win_prob > t1_win_prob:
        predicted_winner = team2
        confidence = "High" if t2_win_prob > 60 else "Medium"
    else:
        predicted_winner = "Draw"
        confidence = "Low"

    expected_t1_goals = round(t1_attack * (1 + (1 / (t2_defense + 0.1))) / 2, 1)
    expected_t2_goals = round(t2_attack * (1 + (1 / (t1_defense + 0.1))) / 2, 1)

    return{
        "match": f"{team1} vs {team2}",
        "predicted_winner": predicted_winner,
        "confidence": confidence,
        "probabilities": {
            team1: f"{t1_win_prob}",
            "draw": f"{draw_prob}",
            team2: f"{t2_win_prob}"
        },
        "expected_score": f"{team1} - {expected_t1_goals} - {expected_t2_goals}",
        "team1_stats": {
            "goals_per_game": t1["goals_per_game"],
            "conceded_per_game": t1["conceded_per_game"],
            "win_rate": t1["win_rate"],
            "wins": t1["wins"]
        },
        "team2_stats": {
            "goals_per_game": t2["goals_per_game"],
            "conceded_per_game": t2["conceded_per_game"],
            "win_rate": t2["win_rate"],
            "wins": t2["wins"]
        }
    }

def get_tournament_standings() -> dict:
    """Get overall tournament standings based on match results.
    
    Returns:
        Dictionary with teams ranked by wins, goals scored, and win rate.
    """
    db = get_db()

    all_matches = list(db.matches.find(
        {"status": "finished"},
        {"home_team": 1, "away_team": 1, "score": 1}
    ))

    teams = {}

    for match in all_matches:
        home = match["home_team"]
        away = match["away_team"]
        home_goals = match["score"]["home"] or 0
        away_goals = match["score"]["away"] or 0

        for team in [home, away]:
            if team not in teams:
                teams[team] = {
                    "team": team,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "points": 0
                }
        
        teams[home]["played"] += 1
        teams[away]["played"] += 1
        teams[home]["goals_for"] += home_goals
        teams[home]["goals_against"] += away_goals
        teams[away]["goals_for"] += away_goals
        teams[away]["goals_against"] += home_goals

        if home_goals > away_goals:
            teams[home]["wins"] += 1
            teams[home]["points"] += 3
            teams[away]["losses"] += 1
        elif away_goals > home_goals:
            teams[away]["wins"] += 1
            teams[away]["points"] += 3
            teams[home]["losses"] += 1
        else:
            teams[home]["draws"] += 1
            teams[away]["draws"] += 1
            teams[home]["points"] += 1
            teams[away]["points"] += 1

    standings = sorted(
        teams.values(),
        key=lambda x: (x["points"], x["goals_for"] - 
            x["goals_against"], x["goals_for"]),
        reverse=True
    )

    for i, team in enumerate(standings):
        team["rank"] = i + 1
        team["goal_difference"] = team["goals_for"] - team["goals_against"]
    
    return{
        "standings": standings[:20],
        "total_teams": len(standings)
    }

def get_live_2026_standings() -> dict:
    """Get current 2026 World Cup group standings from the live API.
    
    Returns:
        Dictionary with current group standings for all 12 groups.
    """
    import requests
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    headers = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}
    base_url = os.getenv("API_FOOTBALL_BASE_URL")

    response = requests.get(
        f"{base_url}/standings",
        headers=headers,
        params={"league": 1, "season": 2026}
    )

    data = response.json()

    if not data["response"]:
        return {"status": "error", "message": "No 2026 standings available yet"}

    groups = []
    standings = data["response"][0]["league"]["standings"]

    for group in standings:
        group_name = group[0]["group"]
        teams = []
        for team in group:
            teams.append({
                "rank": team["rank"],
                "team": team["team"]["name"],
                "played": team["all"]["played"],
                "won": team["all"]["win"],
                "drawn": team["all"]["draw"],
                "lost": team["all"]["lose"],
                "goals_for": team["all"]["goals"]["for"],
                "goals_against": team["all"]["goals"]["against"],
                "goal_difference": team["goalsDiff"],
                "points": team["points"],
                "form": team["form"]
            })
        groups.append({
            "group": group_name,
            "teams": teams
        })
        
        return{
            "season": 2026,
            "total_groups": len(groups),
            "groups": groups
        }

def get_live_2026_top_scorers() -> dict:
    """Get current 2026 World Cup top scorers from the live API.

    Returns:
        Dictionary with current top scorers and their stats.
    """
    import requests
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    headers={"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}
    base_url = os.getenv("API_FOOTBALL_BASE_URL")

    response = requests.get(
        f"{base_url}/players/topscorers",
        headers=headers,
        params={"league": 1, "season": 2026}
    )

    data = response.json()

    if not data["response"]:
        return{
            "status": "pre_tournament",
            "message": "Tournament starts June 11 2026. No goals scored yet.",
            "season" : 2026
        }
    
    scores = []
    for entry in data["response"]:
        player = entry["player"]
        stats = entry["statistics"][0]
        scores.append({
            "name": player["name"],
            "nationality": player["nationality"],
            "age": player["age"],
            "goals": stats["goals"]["total"],
            "assists": stats["goals"]["assists"],
            "appearences": stats["games"]["appearences"],
            "minute": stats["games"]["minutes"],
            "team": stats["team"]["name"]
        })

    return{
        "season": 2026,
        "top_scorers": scores,
        "count": len(scores)
    }

    

get_team_stats_tool = FunctionTool(get_team_stats)
predict_match_tool = FunctionTool(predict_match)
get_tournament_standings_tool = FunctionTool(get_tournament_standings)
get_live_2026_standings_tool = FunctionTool(get_live_2026_standings)
get_live_2026_top_scorers_tool = FunctionTool(get_live_2026_top_scorers)


          
