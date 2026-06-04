# Looker A2A Test Client

This directory contains a simple, standalone client to query the remote Looker Agent-to-Agent (A2A) endpoint using the Google Python ADK.

## Authentication Methods & Agent Cards

We provide two versions of the Agent Card in this directory:

1.  **`agent_card.json` (Used by default)**: Configured for standard HTTP Bearer token headers. Best for developer testing or scripting.
2.  **`agent_card_oauth.json` (Reference only)**: Configured to declare an OAuth 2.0 Authorization Code flow. Best for production environments where end-users authorize access themselves.

---

## Setup Instructions

### 1. Requirements

- Python `>= 3.12`
- `uv` (recommended) or `pip`

### 2. Configure the Agent Cards (`agent_card.json` & `agent_card_oauth.json`)

The agent card files are manifests describing the remote agent and contain template placeholders. Before running the client, you **must** open these files and replace:

- `<LOOKER_URL>`: Your Looker instance domain (e.g. `your-company.looker.com`).
- `<AGENT_ID>`: The unique UUID of the agent you want to query.

Example of a completed `"url"` block inside the JSON:

```json
{
  "name": "looker_agent",
  "url": "https://<LOOKER_URL>/api/4.0/a2a/agents/<AGENT_ID>",
  ...
}
```

### 3. Fetch Looker API Credentials (Bearer Token)

To authorize requests under the standard Bearer flow, you need a Looker API access token.

If you have your Looker **Client ID** and **Client Secret**, you can fetch a short-lived Bearer token using `curl` and `jq`:

```bash
# Replace with your Looker instance host and API credentials
LOOKER_HOST="https://<LOOKER_URL>" # Change to your actual Looker URL
CLIENT_ID="your_client_id"
CLIENT_SECRET="your_client_secret"

curl -s -X POST "${LOOKER_HOST}/api/4.0/login" \
  -d "client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" | jq -r .access_token
```

This command will output the Bearer Token.

### 4. Configure Environment Variables

Create a `.env` file in the `a2a-client` directory and paste your token:

```env
LOOKER_A2A_TOKEN="your-fetched-bearer-token-here"
```

---

## Running the Client

### Option A: Using `uv` (Recommended)

You can run the script instantly with `uv`, which handles environment creation and dependency installation automatically:

```bash
uv run main.py
```

### Option B: Using standard Python Virtual Environment

1.  Create and activate virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -e .
    ```
3.  Run the client:
    ```bash
    python main.py
    ```

---

## OAuth2 A2A Design Reference

For production systems, rather than manually generating tokens and passing them in `.env`, the calling client application or orchestrator performs OAuth2 login flow directly with the user.

For a complete step-by-step walkthrough of generating PKCE challenge codes, handling the login redirect, performing the authorization code token exchange, and passing the token to the A2A client, see the **[OAuth Flow Walkthrough Guide](file:///usr/local/google/home/maluka/ca-demos-and-tools/a2a-client/oauth_guide.md)**.
