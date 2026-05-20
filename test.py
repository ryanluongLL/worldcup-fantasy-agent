import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}

# Check 2026 players
response = requests.get(
    f"{os.getenv('API_FOOTBALL_BASE_URL')}/players",
    headers=headers,
    params={"league": 1, "season": 2026, "page": 1},
)
data = response.json()
print("Players 2026:")
print("  Results:", data["results"])
print("  Errors:", data["errors"])
print("  Paging:", data["paging"])

# Check 2026 fixtures
response2 = requests.get(
    f"{os.getenv('API_FOOTBALL_BASE_URL')}/fixtures",
    headers=headers,
    params={"league": 1, "season": 2026},
)
data2 = response2.json()
print("\nFixtures 2026:")
print("  Results:", data2["results"])
print("  Errors:", data2["errors"])
