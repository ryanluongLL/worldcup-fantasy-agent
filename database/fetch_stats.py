import requests
import os
import time
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_FOOTBALL_BASE_URL")
HEADERS = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}

def get_db():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["worldcup_fantasy"]

POINTS_TABLE = {
    "GK": {"goal": 6, "clean_sheet": 4, "save_set": 1},
    "DEF": {"goal": 6, "clean_sheet": 4},
    "MID": {"goal": 5, "clean_sheet": 1},
    "FWD": {"goal": 4, "clean_sheet": 0},
    "any": {
        "assist": 3,
        "yellow_card": -1,
        "red_card": -3,
        "own_goal": -2,
        "minutes_60": 2,
        "minutes_1": 1
    }
}

def calculate_fantasy_points(position, minutes, goals, assists,
                              clean_sheet, saves, yellow_cards,
                              red_cards, own_goals):
    points = 0
    pos = POINTS_TABLE.get(position, POINTS_TABLE["FWD"])

    if minutes >= 60:
        points += POINTS_TABLE["any"]["minutes_60"]
    elif minutes >= 1:
        points += POINTS_TABLE["any"]["minutes_1"]

    points += goals * pos.get("goal", 4)
    points += assists * POINTS_TABLE["any"]["assist"]

    if clean_sheet and pos.get("clean_sheet", 0) > 0:
        points += pos["clean_sheet"]

    if position == "GK":
        points += (saves // 3) * POINTS_TABLE["GK"]["save_set"]

    points += yellow_cards * POINTS_TABLE["any"]["yellow_card"]
    points += red_cards * POINTS_TABLE["any"]["red_card"]
    points += own_goals * POINTS_TABLE["any"]["own_goal"]

    return points

def fetch_fixture_player_stats(fixture_id: int) -> list:
    """Fetch player stats for a single fixture."""
    response = requests.get(
        f"{BASE_URL}/fixtures/players",
        headers=HEADERS,
        params={"fixture": fixture_id}
    )
    time.sleep(0.5)
    return response.json().get("response", [])

def process_fixture_players(db, match, players_data):
    """Process player stats for one fixture."""
    fixture_id = match["api_fixture_id"]
    match_id = match["_id"]
    matchday = match.get("matchday", 1)

    inserted = 0

    for team_data in players_data:
        team_name = team_data["team"]["name"]
        is_home = team_name == match.get("home_team")

        for player_entry in team_data.get("players", []):
            player_info = player_entry["player"]
            stats = player_entry.get("statistics", [{}])[0]

            games = stats.get("games", {})
            goals_data = stats.get("goals", {})
            cards = stats.get("cards", {})

            minutes = games.get("minutes") or 0
            goals = goals_data.get("total") or 0
            assists = goals_data.get("assists") or 0
            saves = stats.get("goalkeeper", {}).get("saves") or 0
            yellow_cards = cards.get("yellow") or 0
            red_cards = cards.get("red") or 0
            own_goals = goals_data.get("own") or 0

            db_player = db.players.find_one(
                {"api_id": player_info["id"]},
                {"position": 1}
            )
            position = db_player["position"] if db_player else "MID"

            fantasy_points = calculate_fantasy_points(
                position, minutes, goals, assists,
                False, saves, yellow_cards,
                red_cards, own_goals
            )

            stat_doc = {
                "player_id": db_player["_id"] if db_player else None,
                "api_player_id": player_info["id"],
                "player_name": player_info["name"],
                "match_id": match_id,
                "api_fixture_id": fixture_id,
                "matchday": matchday,
                "team": team_name,
                "minutes_played": minutes,
                "goals": goals,
                "assists": assists,
                "clean_sheet": False,
                "saves": saves,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards,
                "own_goals": own_goals,
                "fantasy_points": fantasy_points,
                "updated_at": datetime.now(timezone.utc)
            }

            db.player_stats.update_one(
                {
                    "api_player_id": player_info["id"],
                    "api_fixture_id": fixture_id
                },
                {"$set": stat_doc},
                upsert=True
            )
            inserted += 1

    return inserted

def run_fetch_stats():
    db = get_db()

    fixtures = list(db.matches.find(
        {"status": "finished"},
        {"api_fixture_id": 1}
    ))

    print(f"Found {len(fixtures)} finished matches to process")

    total_stats = 0
    for i, match in enumerate(fixtures):
        fixture_id = match["api_fixture_id"]
        print(f"Processing {i + 1}/{len(fixtures)}: fixture {fixture_id}...")

        players_data = fetch_fixture_player_stats(fixture_id)

        if not players_data:
            print(f"  No data returned")
            continue

        count = process_fixture_players(db, match, players_data)
        total_stats += count
        print(f"  Stored {count} player stats")

    print(f"\nTotal player stats stored: {total_stats}")
    print("Done.")

if __name__ == "__main__":
    run_fetch_stats()