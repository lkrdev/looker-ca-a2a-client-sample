import os
import httpx
import logging
from typing import AsyncGenerator
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.events.event import Event
from google.genai import types
from a2a.client.client import ClientConfig as A2AClientConfig
from a2a.client.client_factory import ClientFactory as A2AClientFactory
from a2a.types import TransportProtocol as A2ATransport

logger = logging.getLogger(__name__)

async def run_agent_query(
    prompt: str,
    invocation_id: str,
    app_name: str,
    user_id: str,
    session_id: str,
    agent_card_path: str,
    token: str,
) -> AsyncGenerator[Event, None]:
    """Runs a single query against the Looker A2A agent and yields response events."""
    logger.info("Configuring A2A connection headers...")
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }

    logger.debug(f"Initializing AsyncClient with timeout 600.0s")
    async with httpx.AsyncClient(headers=auth_headers, timeout=600.0) as client:
        client_config = A2AClientConfig(
            httpx_client=client,
            streaming=True,
            polling=False,
            supported_transports=[A2ATransport.jsonrpc]
        )
        factory = A2AClientFactory(config=client_config)

        logger.debug(f"Using agent card: {agent_card_path}")
        remote_agent = RemoteA2aAgent(
            name="looker_agent",
            agent_card=agent_card_path,
            a2a_client_factory=factory
        )

        logger.info(f"Creating session (app={app_name}, user={user_id}, session={session_id})")
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

        logger.debug("Appending user content message event to session...")
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        user_event = Event(
            invocation_id=invocation_id,
            author="user",
            content=user_content
        )
        await session_service.append_event(session, user_event)

        logger.debug(f"Creating invocation context (id={invocation_id})")
        ctx = InvocationContext(
            invocation_id=invocation_id,
            session_service=session_service,
            agent=remote_agent,
            session=session,
            user_content=user_content
        )

        logger.info("Executing remote agent...")
        async for event in remote_agent.run_async(ctx):
            yield event
