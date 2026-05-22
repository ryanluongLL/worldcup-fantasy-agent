import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from agent.agent import root_agent


async def test():
    runner = InMemoryRunner(agent=root_agent, app_name="worldcup_fantasy")

    session = await runner.session_service.create_session(
        app_name="worldcup_fantasy", user_id="test_user"
    )

    message = Content(
        role="user",
        parts=[Part(text="Suggest a transfer for user 'luan' matchday 1, then recommend a captain, then compare Mbappe vs Messi, then show me the top 5 in-form players.")]
    )

    print("Sending message...")

    async for event in runner.run_async(
        user_id="test_user", session_id=session.id, new_message=message
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"Agent: {part.text}")


asyncio.run(test())
