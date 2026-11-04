"""Google OAuth 2.0 Authentication Service."""

import os
import json
import threading
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config.constants import GOOGLE_TASKS_SCOPES, CREDENTIALS_FILE_PATH
from utils.credentials_manager import CredentialsManager
from utils.config_manager import config_manager
from utils.logger import logger

class GoogleAuthService:
    """Manages Google OAuth 2.0 authentication, refresh, and profile retrieval."""

    def __init__(self):
        self._credentials: Optional[Credentials] = None
        self._lock = threading.Lock()
        self.on_auth_changed: Optional[Callable[[bool, Optional[str]], None]] = None

    def get_credentials_path(self) -> Optional[Path]:
        """Locates the OAuth client secrets credentials.json."""
        # 1. In AppData
        if CREDENTIALS_FILE_PATH.exists():
            return CREDENTIALS_FILE_PATH
        # 2. In current directory or parent directory
        local_creds = Path("credentials.json")
        if local_creds.exists():
            return local_creds
        return None

    def is_authenticated(self) -> bool:
        """Quick check if active valid credentials are available."""
        creds = self.get_valid_credentials()
        return creds is not None and creds.valid

    def get_valid_credentials(self) -> Optional[Credentials]:
        """Returns valid Credentials, automatically refreshing expired tokens if possible."""
        with self._lock:
            if self._credentials and self._credentials.valid:
                return self._credentials

            token_data = CredentialsManager.load_tokens()
            if not token_data:
                return None

            try:
                creds = Credentials.from_authorized_user_info(token_data, GOOGLE_TASKS_SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Access token expired. Refreshing using refresh_token...")
                    creds.refresh(Request())
                    CredentialsManager.save_tokens(json.loads(creds.to_json()))
                    logger.info("Access token refreshed and persisted.")

                if creds and creds.valid:
                    self._credentials = creds
                    return self._credentials
            except Exception as e:
                logger.error(f"Failed to load or refresh stored credentials: {e}")
                return None

            return None

    def authenticate_interactive(self, credentials_file: Optional[Path] = None, client_config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Launches Google OAuth browser flow on localhost loopback.
        Supports both credentials.json file path and in-memory client configuration dict.
        """
        try:
            flow = None
            if client_config:
                flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_TASKS_SCOPES)
            else:
                creds_file = credentials_file or self.get_credentials_path()
                if not creds_file or not Path(creds_file).exists():
                    return False, "Google OAuth credentials.json file was not found. Please provide it in Settings or place it in the app directory."
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), GOOGLE_TASKS_SCOPES)

            # Run local server for OAuth redirect
            logger.info("Opening browser for Google Tasks OAuth login...")
            creds = flow.run_local_server(
                host="localhost",
                port=0,
                authorization_prompt_message="Please authorize NudgeDesk in your web browser...",
                success_message="Authentication successful! You can now close this tab and return to NudgeDesk.",
                open_browser=True
            )

            if not creds or not creds.valid:
                return False, "Authentication did not complete successfully."

            self._credentials = creds
            token_dict = json.loads(creds.to_json())
            CredentialsManager.save_tokens(token_dict)

            # Retrieve user profile info (email and display name)
            email, name = self._fetch_user_profile(creds)
            config_manager.set("account_email", email)
            config_manager.set("account_name", name)

            logger.info(f"Successfully authenticated as {email} ({name}).")

            if self.on_auth_changed:
                self.on_auth_changed(True, email)

            return True, f"Successfully connected to Google Tasks as {email}"

        except Exception as e:
            logger.error(f"Interactive authentication failed: {e}")
            return False, f"Authentication error: {str(e)}"

    def _fetch_user_profile(self, creds: Credentials) -> Tuple[Optional[str], Optional[str]]:
        """Fetches the user's primary email and name via Google userinfo API."""
        try:
            service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
            user_info = service.userinfo().get().execute()
            email = user_info.get("email")
            name = user_info.get("name")
            return email, name
        except Exception as e:
            logger.warning(f"Could not retrieve profile info: {e}")
            return None, None

    def sign_out(self) -> None:
        """Clears local tokens and disconnects Google account."""
        with self._lock:
            self._credentials = None
            CredentialsManager.clear_tokens()
            config_manager.set("account_email", None)
            config_manager.set("account_name", None)
            logger.info("User signed out.")
            if self.on_auth_changed:
                self.on_auth_changed(False, None)

google_auth = GoogleAuthService()

