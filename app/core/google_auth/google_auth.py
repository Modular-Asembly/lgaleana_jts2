import os
from typing import Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# OAuth token endpoint for Google
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

def get_google_oauth_credentials() -> Credentials:
    """
    Obtains Google OAuth credentials by using environment variables:
      - OAUTH_CLIENT_ID
      - OAUTH_CLIENT_SECRET
      - OAUTH_REFRESH_TOKEN

    Creates a Credentials object with no initial access token and refreshes it immediately,
    returning valid credentials with an access token.
    
    Returns:
        A google.oauth2.credentials.Credentials instance with a valid access token.
    
    Raises:
        EnvironmentError: If one or more required environment variables are not set.
        google.auth.exceptions.RefreshError: If the token refresh operation fails.
    """
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    refresh_token = os.getenv("OAUTH_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        raise EnvironmentError("One or more required environment variables (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REFRESH_TOKEN) are not set.")

    # Construct a credentials object without an access token
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Refresh the access token using a Request
    creds.refresh(Request())
    return creds

def get_access_token() -> str:
    """
    Obtains a valid Google OAuth access token.
    
    Returns:
        The access token as a string.
    
    Raises:
        EnvironmentError: If required environment variables are missing.
        google.auth.exceptions.RefreshError: If token refresh fails.
    """
    creds = get_google_oauth_credentials()
    return creds.token

def get_google_auth_headers() -> Dict[str, str]:
    """
    Returns HTTP headers for authenticating against Google APIs.
    The header contains the Bearer token.
    
    Returns:
        A dictionary with the Authorization header.
    """
    access_token = get_access_token()
    return {"Authorization": f"Bearer {access_token}"}
