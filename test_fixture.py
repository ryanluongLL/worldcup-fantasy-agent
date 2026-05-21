import requests
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

headers = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}

# Try fetching fixture players directly
response = requests.get(
    f"{os.getenv('API_FOOTBALL_BASE_URL')}/fixtures/players",
    headers=headers,
    params={"fixture": 855736}
)

data = response.json()
print("Results:", data["results"])
print("Errors:", data["errors"])
if data["response"]:
    print("First entry keys:", list(data["response"][0].keys()))