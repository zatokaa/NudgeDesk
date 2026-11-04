"""Unit tests for CredentialsManager and DPAPI protection."""

import unittest
from utils.credentials_manager import CredentialsManager, _dpapi_encrypt, _dpapi_decrypt

class TestCredentialsManager(unittest.TestCase):

    def test_dpapi_roundtrip(self):
        sample_secret = b"Google_OAuth_Super_Secret_Token_String_12345"
        encrypted = _dpapi_encrypt(sample_secret)
        self.assertNotEqual(sample_secret, encrypted)
        
        decrypted = _dpapi_decrypt(encrypted)
        self.assertEqual(sample_secret, decrypted)

    def test_save_load_tokens(self):
        sample_tokens = {
            "token": "ya29.sample_access_token",
            "refresh_token": "1//sample_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id.apps.googleusercontent.com",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/tasks"]
        }

        saved = CredentialsManager.save_tokens(sample_tokens)
        self.assertTrue(saved)

        loaded = CredentialsManager.load_tokens()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["token"], sample_tokens["token"])
        self.assertEqual(loaded["refresh_token"], sample_tokens["refresh_token"])

        # Test clearing
        CredentialsManager.clear_tokens()
        loaded_after_clear = CredentialsManager.load_tokens()
        self.assertIsNone(loaded_after_clear)

if __name__ == "__main__":
    unittest.main()

