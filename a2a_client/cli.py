import asyncio
import logging
import os
import sys
from pathlib import Path
import typer
from dotenv import load_dotenv

from a2a_client.client import run_agent_query

app = typer.Typer(
    help="CLI for chatting with Looker A2A agent.",
    no_args_is_help=True,
)

# Configure standard logging to output to stderr
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("a2a_client")

@app.command()
def version():
    """Show the version of the A2A client."""
    typer.echo("0.1.0")

@app.command()
def chat(
    prompt: str = typer.Option(
        ...,
        "--prompt",
        "-p",
        help="The prompt to send to the A2A agent.",
    ),
    invocation_id: str = typer.Option(
        "test_invocation_123",
        "--invocation-id",
        "-i",
        help="Invocation ID context.",
    ),
    app_name: str = typer.Option(
        "test_app",
        "--app-name",
        help="App name identifier for the session.",
    ),
    user_id: str = typer.Option(
        "test_user",
        "--user-id",
        help="User ID identifier for the session.",
    ),
    session_id: str = typer.Option(
        "test_session_id",
        "--session-id",
        help="Session ID identifier.",
    ),
    agent_card: str = typer.Option(
        "agent_card.json",
        "--agent-card",
        help="Path to the local agent_card.json file.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose info logging.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable full debug logging.",
    ),
):
    """Chat with the Looker A2A agent."""
    # Set logging level
    if debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("a2a_client.client").setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
        logging.getLogger("a2a_client.client").setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
        logging.getLogger("a2a_client.client").setLevel(logging.WARNING)

    # Load environment variables (from local .env or system environment)
    load_dotenv()
    token = os.environ.get("LOOKER_A2A_TOKEN")
    if not token:
        typer.echo(
            "Error: LOOKER_A2A_TOKEN environment variable is not set.\n"
            "Please set it in your environment or configure it in a .env file.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Resolve agent_card absolute path
    agent_card_path = Path(agent_card)
    if not agent_card_path.exists():
        # Fallback to the directory containing the package parent (the CLI project root)
        project_root = Path(__file__).resolve().parent.parent
        agent_card_path = project_root / agent_card

    if not agent_card_path.exists():
        typer.echo(
            f"Error: Agent card file not found at '{agent_card}' or '{agent_card_path}'.",
            err=True,
        )
        raise typer.Exit(code=1)

    async def _run():
        try:
            async for event in run_agent_query(
                prompt=prompt,
                invocation_id=invocation_id,
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                agent_card_path=str(agent_card_path),
                token=token,
            ):
                if event.error_message:
                    typer.echo(f"\nError received from agent: {event.error_message}", err=True)
                elif event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            # Print agent's streaming output directly to stdout
                            sys.stdout.write(part.text)
                            sys.stdout.flush()
            typer.echo()
        except Exception as e:
            typer.echo(f"\nFailed to communicate with remote agent: {e}", err=True)
            if debug:
                raise
            raise typer.Exit(code=1)

    asyncio.run(_run())

if __name__ == "__main__":
    app()
