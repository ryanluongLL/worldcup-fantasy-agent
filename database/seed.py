import requests
import os
import time
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_FOOTBALL_BASE_URL")
HEADERS = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}
LEAGUE = int(os.getenv("API_FOOTBALL_LEAGUE", 1))
SEASON = int(os.getenv("API_FOOTBALL_SEASON", 2022))


def get_database():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["worldcup_fantasy"]


def api_get(endpoint, params):
    """Single API call with rate limit protection."""
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params)
    time.sleep(0.5)
    return response.json()


def seed_players_2026(db):
    """Pull 2026 World Cup squads and store as players."""
    print("\nSeeding 2026 players...")

    page = 1
    total_inserted = 0

    while True:
        data = api_get("players", {"league": LEAGUE, "season": SEASON, "page": page})

        players = data.get("response", [])
        if not players:
            break

        for entry in players:
            player = entry["player"]
            stats = entry["statistics"][0] if entry["statistics"] else {}

            position_map = {
                "Goalkeeper": "GK",
                "Defender": "DEF",
                "Midfielder": "MID",
                "Attacker": "FWD",
            }

            raw_position = stats.get("games", {}).get("position", "MID")
            position = position_map.get(raw_position, "MID")

            player_doc = {
                "api_id": player["id"],
                "name": player["name"],
                "firstname": player["firstname"],
                "lastname": player["lastname"],
                "age": player["age"],
                "nationality": player["nationality"],
                "photo": player["photo"],
                "position": position,
                "club": stats.get("team", {}).get("name", "Unknown"),
                "is_available": True,
                "price": assign_price(position),
                "season_2026": True,
                "created_at": datetime.now(timezone.utc),
            }

            db.players.update_one(
                {"api_id": player["id"]}, {"$set": player_doc}, upsert=True
            )
            total_inserted += 1

        print(f"  Page {page}: {len(players)} players processed")

        if data["paging"]["current"] >= data["paging"]["total"]:
            break

        page += 1

    print(f"Total 2026 players seeded: {total_inserted}")


def assign_price(position):
    """Assign default fantasy price by position."""
    prices = {"GK": 5.0, "DEF": 5.5, "MID": 7.0, "FWD": 8.0}
    return prices.get(position, 6.0)


def seed_matches_2026(db):
    """Pull 2026 World Cup fixtures."""
    print("\nSeeding 2026 fixtures...")

    data = api_get("fixtures", {"league": LEAGUE, "season": SEASON})

    fixtures = data.get("response", [])
    total_inserted = 0

    for fixture in fixtures:
        f = fixture["fixture"]
        teams = fixture["teams"]
        goals = fixture["goals"]
        league = fixture["league"]

        stage_map = {
            "Group Stage": "group",
            "Round of 32": "round_of_32",
            "Round of 16": "round_of_16",
            "Quarter-finals": "quarter_final",
            "Semi-finals": "semi_final",
            "3rd Place Final": "third_place",
            "Final": "final",
        }

        raw_round = league.get("round", "Group Stage - 1")
        stage = "group"
        for key in stage_map:
            if key in raw_round:
                stage = stage_map[key]
                break

        status_map = {
            "NS": "scheduled",
            "1H": "live",
            "HT": "live",
            "2H": "live",
            "FT": "finished",
            "AET": "finished",
            "PEN": "finished",
        }

        match_doc = {
            "api_fixture_id": f["id"],
            "matchday": extract_matchday(raw_round),
            "round": raw_round,
            "stage": stage,
            "home_team": teams["home"]["name"],
            "home_team_id": teams["home"]["id"],
            "away_team": teams["away"]["name"],
            "away_team_id": teams["away"]["id"],
            "date": datetime.fromisoformat(f["date"].replace("Z", "+00:00")),
            "venue": f["venue"]["name"],
            "city": f["venue"]["city"],
            "status": status_map.get(f["status"]["short"], "scheduled"),
            "score": {"home": goals["home"], "away": goals["away"]},
            "season": SEASON,
            "updated_at": datetime.now(timezone.utc),
        }

        db.matches.update_one(
            {"api_fixture_id": f["id"]}, {"$set": match_doc}, upsert=True
        )
        total_inserted += 1

    print(f"Total 2026 fixtures seeded: {total_inserted}")


def extract_matchday(round_string):
    """Extract matchday number from round string."""
    try:
        return int(round_string.split("-")[-1].strip())
    except Exception:
        return 1


def seed_historical_stats_2022(db):
    """Pull 2022 top scorers and assists as historical performance data."""
    print("\nSeeding 2022 historical stats...")

    # Top scorers
    scorers_data = api_get("players/topscorers", {"league": LEAGUE, "season": SEASON})

    for entry in scorers_data.get("response", []):
        player = entry["player"]
        stats = entry["statistics"][0]

        db.players.update_one(
            {"api_id": player["id"]},
            {
                "$set": {
                    "historical_2022": {
                        "goals": stats["goals"]["total"],
                        "assists": stats["goals"]["assists"],
                        "appearances": stats["games"]["appearences"],
                        "minutes": stats["games"]["minutes"],
                        "rating": stats["games"]["rating"],
                        "yellow_cards": stats["cards"]["yellow"],
                        "red_cards": stats["cards"]["red"],
                    }
                }
            },
            upsert=False,
        )

    print(f"  2022 top scorers processed: {len(scorers_data.get('response', []))}")

    # Top assists
    assists_data = api_get("players/topassists", {"league": LEAGUE, "season": SEASON})

    for entry in assists_data.get("response", []):
        player = entry["player"]
        stats = entry["statistics"][0]

        db.players.update_one(
            {"api_id": player["id"]},
            {"$set": {"historical_2022.assists": stats["goals"]["assists"]}},
            upsert=False,
        )

    print(f"  2022 top assists processed: {len(assists_data.get('response', []))}")


def seed_matchdays(db):
    """Create matchday documents for 2026."""
    print("\nSeeding matchdays...")

    matchdays = []

    # Group stage has 3 matchdays
    for i in range(1, 4):
        matchdays.append(
            {
                "matchday_number": i,
                "stage": "group",
                "status": "upcoming",
                "deadline": None,
                "season": SEASON,
                "created_at": datetime.now(timezone.utc),
            }
        )

    # Knockout rounds
    knockout_stages = [
        (4, "round_of_32"),
        (5, "round_of_16"),
        (6, "quarter_final"),
        (7, "semi_final"),
        (8, "final"),
    ]

    for matchday_num, stage in knockout_stages:
        matchdays.append(
            {
                "matchday_number": matchday_num,
                "stage": stage,
                "status": "upcoming",
                "deadline": None,
                "season": SEASON,
                "created_at": datetime.now(timezone.utc),
            }
        )

    for matchday in matchdays:
        db.matchdays.update_one(
            {"matchday_number": matchday["matchday_number"]},
            {"$set": matchday},
            upsert=True,
        )

    print(f"Total matchdays seeded: {len(matchdays)}")


def run_seed():
    db = get_database()

    print("Starting data pipeline...")
    print(f"Requests will be made carefully to stay within 100/day limit.")

    seed_players_2026(db)
    seed_matches_2026(db)
    seed_historical_stats_2022(db)
    seed_matchdays(db)

    print("\nSeed complete.")


if __name__ == "__main__":
    run_seed()
