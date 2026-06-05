# OAuth 2.0 PKCE Flow for Looker A2A Clients

This guide outlines how a client application implements the OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) to obtain user access tokens and query the A2A agent.

For a complete, working reference implementation of a Python backend executing this Looker OAuth login flow, see:
👉 **[Looker Developer Relations OAuth Python Demo](https://github.com/looker-open-source/devrel-demos/tree/main/oauth-python)**

---

## Architectural Flow

1. **Initiate Flow**: The user clicks "Connect to Looker" in the browser. The Client Application generates a PKCE `code_verifier` and its `code_challenge`.
2. **Authorize**: The Client Application redirects the user's browser to the Looker Authorization URL. The user logs in and approves the `cors-api` scope.
3. **Authorization Callback**: Looker redirects the user back to the Client Application callback URL with an temporary `authorization_code`.
4. **Token Exchange**: The Client Application backend makes a direct `POST` request to Looker's token endpoint (`/api/token`), exchanging the code (along with the original `code_verifier`) for a Bearer `access_token`.
5. **A2A Execution**: The Client Application wraps the user's token in the HTTP Authorization headers and calls the remote A2A Agent.
6. **Results**: The A2A Agent executes queries against Looker and streams the response back to the Client Application, which displays the results to the user.


---

## The Core OAuth Steps

### Step 1: Initiate Redirect with PKCE
Your application backend generates a random `code_verifier` and its SHA-256 hash `code_challenge`. 

Store the `code_verifier` in the user's secure session (e.g. cookie or backend session), and redirect their browser to Looker:

```
https://<YOUR_LOOKER_HOST>/oauth/authorize?
  response_type=code&
  client_id=<YOUR_CLIENT_ID>&
  redirect_uri=https://<YOUR_APP_CALLBACK>&
  scope=cors-api&
  code_challenge_method=S256&
  code_challenge=<CODE_CHALLENGE>&
  state=<RANDOM_CSRF_STATE>
```

### Step 2: Exchange Authorization Code for Access Token
Looker redirects back to your callback URI: `https://<YOUR_APP_CALLBACK>?code=<AUTHORIZATION_CODE>&state=<STATE>`.

Verify the `state` matches your session, retrieve the stored `code_verifier`, and send a `POST` request to Looker's token endpoint to fetch the token:

*   **Endpoint**: `POST https://<YOUR_LOOKER_HOST>/api/token`
*   **Body Content-Type**: `application/x-www-form-urlencoded`
*   **Payload**:
    ```ini
    grant_type=authorization_code
    client_id=<YOUR_CLIENT_ID>
    code=<AUTHORIZATION_CODE>
    redirect_uri=https://<YOUR_APP_CALLBACK>
    code_verifier=<CODE_VERIFIER>
    ```

---

## Passing Token to the A2A Client (ADK)

Once the application has the dynamic `access_token` for the user, it injects it into the `RemoteA2aAgent` client via a custom HTTPX client:

```python
import httpx
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

async def query_agent_for_user(user_query: str, access_token: str):
    # Configure headers containing the user's specific access token
    auth_headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Run the query using a scoped HTTP client
    async with httpx.AsyncClient(headers=auth_headers, timeout=600.0) as client:
        remote_agent = RemoteA2aAgent(
            name="looker_agent",
            agent_card="agent_card_oauth.json",
            httpx_client=client
        )
        
        # Now execute remote_agent.run_async(ctx) as usual
```
