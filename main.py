import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from agent.agent import root_agent

if __name__ == "__main__":
    print("World Cup Fantasy Agent ready.")
    print("Run 'adk web' to start the agent interface.")
