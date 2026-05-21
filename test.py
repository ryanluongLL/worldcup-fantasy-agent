import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {"x-apisports-key": os.getenv("API_FOOTBALL_KEY")}

response = requests.get(f"{os.getenv('API_FOOTBALL_BASE_URL')}/status", headers=headers)

data = response.json()
requests_info = data["response"]["requests"]
print(f"Used today: {requests_info['current']} / {requests_info['limit_day']}")
print(f"Remaining: {requests_info['limit_day'] - requests_info['current']}")
