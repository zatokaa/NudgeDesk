"""Secure token and credential management using Windows Credential Manager / DPAPI."""

import os
import json
import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Any
from utils.logger import logger
from config.constants import APPDATA_DIR

try:
    import keyring
except ImportError:
    keyring = None

SERVICE_NAME = "NudgeDesk_GoogleTasks"
TOKEN_KEY = "oauth_token_data"
CLIENT_CONFIG_KEY = "client_config_data"

# Windows DPAPI fallback helpers
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def _dpapi_encrypt(data: bytes) -> bytes:
    """Encrypts bytes using current user Windows DPAPI."""
    try:
        data_in = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
        data_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(data_in),
            "NudgeDesk Secret",
            None,
            None,
            None,
            0,
            ctypes.byref(data_out)
        ):
            encrypted = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return encrypted
    except Exception as e:
        logger.warning(f"DPAPI encryption failed: {e}")
    return data

def _dpapi_decrypt(encrypted_data: bytes) -> bytes:
    """Decrypts bytes using current user Windows DPAPI."""
    try:
        data_in = DATA_BLOB(len(encrypted_data), ctypes.create_string_buffer(encrypted_data, len(encrypted_data)))
        data_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(data_in),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(data_out)
        ):
            decrypted = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return decrypted
    except Exception as e:
        logger.warning(f"DPAPI decryption failed: {e}")
    return encrypted_data

class CredentialsManager:
    """Handles secure storage of Google OAuth tokens and API secrets."""
    
    _secure_file = APPDATA_DIR / "vault.dat"

    @classmethod
    def save_tokens(cls, token_data: Dict[str, Any]) -> bool:
        """Stores token JSON dictionary securely."""
        data_str = json.dumps(token_data)
        try:
            if keyring:
                keyring.set_password(SERVICE_NAME, TOKEN_KEY, data_str)
                logger.info("Saved OAuth tokens in Windows Credential Manager.")
                return True
        except Exception as e:
            logger.warning(f"Could not save tokens to keyring: {e}. Falling back to DPAPI file.")

        # Fallback to DPAPI encrypted file
        try:
            encrypted = _dpapi_encrypt(data_str.encode("utf-8"))
            cls._secure_file.write_bytes(encrypted)
            logger.info("Saved OAuth tokens in DPAPI-protected file.")
            return True
        except Exception as ex:
            logger.error(f"Failed to save tokens securely: {ex}")
            return False

    @classmethod
    def load_tokens(cls) -> Optional[Dict[str, Any]]:
        """Retrieves securely stored OAuth tokens."""
        # 1. Try keyring
        if keyring:
            try:
                data_str = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
                if data_str:
                    return json.loads(data_str)
            except Exception as e:
                logger.warning(f"Error loading tokens from keyring: {e}")

        # 2. Try DPAPI file
        if cls._secure_file.exists():
            try:
                encrypted = cls._secure_file.read_bytes()
                decrypted = _dpapi_decrypt(encrypted).decode("utf-8")
                return json.loads(decrypted)
            except Exception as ex:
                logger.error(f"Failed to decrypt token file: {ex}")

        return None

    @classmethod
    def clear_tokens(cls) -> None:
        """Removes stored tokens upon sign-out."""
        if keyring:
            try:
                keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
            except Exception:
                pass
        if cls._secure_file.exists():
            try:
                cls._secure_file.unlink()
            except Exception:
                pass
        logger.info("Cleared stored tokens.")

    @classmethod
    def save_client_credentials(cls, client_id: str, client_secret: str) -> bool:
        """Saves custom OAuth client credentials."""
        data = json.dumps({"client_id": client_id, "client_secret": client_secret})
        try:
            if keyring:
                keyring.set_password(SERVICE_NAME, CLIENT_CONFIG_KEY, data)
                return True
        except Exception:
            pass
        return False

    @classmethod
    def load_client_credentials(cls) -> Optional[Dict[str, str]]:
        """Loads custom OAuth client credentials if previously saved."""
        if keyring:
            try:
                data_str = keyring.get_password(SERVICE_NAME, CLIENT_CONFIG_KEY)
                if data_str:
                    return json.loads(data_str)
            except Exception:
                pass
        return None

