from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os

load_dotenv()


def get_database():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["worldcup_fantasy"]


def create_collections_and_indexes():
    db = get_database()

    existing = db.list_collection_names()
    collections = [
        "users",
        "players",
        "matches",
        "player_stats",
        "lineups",
        "scores",
        "matchdays",
    ]

    for collection in collections:
        if collection in existing:
            db.drop_collection(collection)
            print(f"Dropped existing: {collection}")

    # Users collection
    db.create_collection(
        "users",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["username", "email", "team_name", "created_at"],
                "properties": {
                    "username": {
                        "bsonType": "string",
                        "description": "Unique username",
                    },
                    "email": {
                        "bsonType": "string",
                        "description": "User email address",
                    },
                    "team_name": {
                        "bsonType": "string",
                        "description": "Fantasy team name",
                    },
                    "total_points": {
                        "bsonType": "int",
                        "description": "Cumulative fantasy points",
                    },
                    "created_at": {"bsonType": "date"},
                },
            }
        },
    )
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True)
    print("Created: users")

    # Players collection
    db.create_collection(
        "players",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["name", "position", "nationality", "club"],
                "properties": {
                    "name": {"bsonType": "string"},
                    "position": {
                        "bsonType": "string",
                        "enum": ["GK", "DEF", "MID", "FWD"],
                    },
                    "nationality": {"bsonType": "string"},
                    "club": {"bsonType": "string"},
                    "price": {
                        "bsonType": "double",
                        "description": "Fantasy price in millions",
                    },
                    "is_available": {
                        "bsonType": "bool",
                        "description": "False if injured or suspended",
                    },
                },
            }
        },
    )
    db.players.create_index([("name", ASCENDING)])
    db.players.create_index([("position", ASCENDING)])
    db.players.create_index([("nationality", ASCENDING)])
    print("Created: players")

    # Matches collection
    db.create_collection(
        "matches",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["matchday", "home_team", "away_team", "date", "status"],
                "properties": {
                    "matchday": {"bsonType": "int", "description": "Round number"},
                    "home_team": {"bsonType": "string"},
                    "away_team": {"bsonType": "string"},
                    "date": {"bsonType": "date"},
                    "status": {
                        "bsonType": "string",
                        "enum": ["scheduled", "live", "finished"],
                    },
                    "score": {
                        "bsonType": "object",
                        "properties": {
                            "home": {"bsonType": "int"},
                            "away": {"bsonType": "int"},
                        },
                    },
                    "stage": {
                        "bsonType": "string",
                        "enum": [
                            "group",
                            "round_of_32",
                            "round_of_16",
                            "quarter_final",
                            "semi_final",
                            "third_place",
                            "final",
                        ],
                    },
                },
            }
        },
    )
    db.matches.create_index([("matchday", ASCENDING)])
    db.matches.create_index([("status", ASCENDING)])
    db.matches.create_index([("date", ASCENDING)])
    print("Created: matches")

    # Player stats collection (one document per player per match)
    db.create_collection(
        "player_stats",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["player_id", "match_id", "matchday"],
                "properties": {
                    "player_id": {"bsonType": "objectId"},
                    "match_id": {"bsonType": "objectId"},
                    "matchday": {"bsonType": "int"},
                    "minutes_played": {"bsonType": "int"},
                    "goals": {"bsonType": "int"},
                    "assists": {"bsonType": "int"},
                    "clean_sheet": {"bsonType": "bool"},
                    "saves": {"bsonType": "int"},
                    "yellow_cards": {"bsonType": "int"},
                    "red_cards": {"bsonType": "int"},
                    "own_goals": {"bsonType": "int"},
                    "fantasy_points": {
                        "bsonType": "int",
                        "description": "Calculated points for this match",
                    },
                },
            }
        },
    )
    db.player_stats.create_index([("player_id", ASCENDING)])
    db.player_stats.create_index([("match_id", ASCENDING)])
    db.player_stats.create_index([("matchday", ASCENDING)])
    db.player_stats.create_index(
        [("player_id", ASCENDING), ("match_id", ASCENDING)], unique=True
    )
    print("Created: player_stats")

    # Lineups collection (user's selected team per matchday)
    db.create_collection(
        "lineups",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "matchday", "starters", "bench"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "matchday": {"bsonType": "int"},
                    "starters": {
                        "bsonType": "array",
                        "minItems": 11,
                        "maxItems": 11,
                        "description": "11 starting player IDs",
                    },
                    "bench": {
                        "bsonType": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "description": "4 bench player IDs",
                    },
                    "formation": {
                        "bsonType": "string",
                        "description": "e.g. 4-3-3, 4-4-2",
                    },
                    "agent_recommendation": {
                        "bsonType": "string",
                        "description": "Gemini reasoning for this lineup",
                    },
                    "locked": {
                        "bsonType": "bool",
                        "description": "True once the matchday starts",
                    },
                },
            }
        },
    )
    db.lineups.create_index(
        [("user_id", ASCENDING), ("matchday", ASCENDING)], unique=True
    )
    print("Created: lineups")

    # Scores collection (user points per matchday)
    db.create_collection(
        "scores",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "matchday", "points"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "matchday": {"bsonType": "int"},
                    "points": {"bsonType": "int"},
                    "breakdown": {
                        "bsonType": "array",
                        "description": "Points per player for transparency",
                    },
                },
            }
        },
    )
    db.scores.create_index([("user_id", ASCENDING)])
    db.scores.create_index([("matchday", ASCENDING)])
    db.scores.create_index(
        [("user_id", ASCENDING), ("matchday", ASCENDING)], unique=True
    )
    print("Created: scores")

    # Matchdays collection
    db.create_collection(
        "matchdays",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["matchday_number", "stage", "status"],
                "properties": {
                    "matchday_number": {"bsonType": "int"},
                    "stage": {
                        "bsonType": "string",
                        "enum": [
                            "group",
                            "round_of_32",
                            "round_of_16",
                            "quarter_final",
                            "semi_final",
                            "third_place",
                            "final",
                        ],
                    },
                    "deadline": {
                        "bsonType": ["date", "null"],
                        "description": "Transfer deadline before matchday starts",
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["upcoming", "active", "completed"],
                    },
                },
            }
        },
    )
    db.matchdays.create_index([("matchday_number", ASCENDING)], unique=True)
    print("Created: matchdays")

    print("\nAll collections and indexes created successfully.")


if __name__ == "__main__":
    create_collections_and_indexes()
