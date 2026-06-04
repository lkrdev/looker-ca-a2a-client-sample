import asyncio
import os
import httpx
from dotenv import load_dotenv
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.events.event import Event
from google.genai import types
from a2a.client.client import ClientConfig as A2AClientConfig
from a2a.client.client_factory import ClientFactory as A2AClientFactory
from a2a.types import TransportProtocol as A2ATransport

# Load environment variables from .env file if present
load_dotenv()

async def main():
    token = os.environ.get("LOOKER_A2A_TOKEN")
    if not token:
        print("Error: LOOKER_A2A_TOKEN environment variable is not set.")
        print("Please set it or configure it in a .env file.")
        return
    
    # Locate local agent_card.json in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    agent_card_path = os.path.join(script_dir, "agent_card.json")

    # 1. Configure the HTTP Client with the Bearer Token
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 2. Use a custom httpx AsyncClient to pass the headers and timeout settings
    async with httpx.AsyncClient(headers=auth_headers, timeout=600.0) as client:
        # Define client configuration to enable streaming
        client_config = A2AClientConfig(
            httpx_client=client,
            streaming=True,
            polling=False,
            supported_transports=[A2ATransport.jsonrpc]
        )
        factory = A2AClientFactory(config=client_config)

        # 3. Instantiate the Remote A2A Agent using the local card configuration and factory
        remote_agent = RemoteA2aAgent(
            name="looker_agent",
            agent_card=agent_card_path,
            a2a_client_factory=factory
        )
        
        # 4. Prepare the session and services
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session_id"
        )
        
        # Create user message event and append it to the session
        user_content = types.Content(
            role="user",
            parts=[types.Part(text="show me FW42 report for Dresses")]
        )
        user_event = Event(
            invocation_id="test_invocation_123",
            author="user",
            content=user_content
        )
        await session_service.append_event(session, user_event)
        
        # Create Invocation Context
        ctx = InvocationContext(
            invocation_id="test_invocation_123",
            session_service=session_service,
            agent=remote_agent,
            session=session,
            user_content=user_content
        )
        
        # 5. Run the agent and print stream response
        print("Sending query to Looker A2A agent...")
        try:
            async for event in remote_agent.run_async(ctx):
                if event.error_message:
                    print(f"\nError received: {event.error_message}")
                elif event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(part.text + "\n", end="", flush=True)
            print()
        except Exception as e:
            print(f"\nFailed to communicate with remote agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
