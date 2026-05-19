from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()


def test_connection():
    uri = os.getenv("MONGODB_URI")

    if not uri:
        print("Error: MONGODB_URI not found in .env file")
        return

    try:
        client = MongoClient(uri)
        db = client["worldcup_fantasy"]

        db["connection_test"].insert_one(
            {"status": "connected", "project": "worldcup-fantasy-agent"}
        )

        result = db["connection_test"].find_one({"status": "connected"})
        print(f"Connection successful: {result}")

        db["connection_test"].drop()
        print("Test collection cleaned up")

        client.close()
    except Exception as e:
        print(f"Connection failed : {e}")


if __name__ == "__main__":
    test_connection()
