"""Unit tests for configuration manager."""

import unittest
import tempfile
from pathlib import Path
from utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "config.json"
        
        # Monkey patch CONFIG_FILE_PATH for test
        import utils.config_manager as cm
        self.original_path = cm.CONFIG_FILE_PATH
        cm.CONFIG_FILE_PATH = self.config_file
        self.cm = ConfigManager()

    def tearDown(self):
        import utils.config_manager as cm
        cm.CONFIG_FILE_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_default_values(self):
        self.assertEqual(self.cm.get("theme_mode"), "dark")
        self.assertEqual(self.cm.get("sync_interval"), 300)
        self.assertTrue(self.cm.get("auto_sync"))

    def test_set_and_persist(self):
        self.cm.set("theme_mode", "light")
        self.cm.set("sync_interval", 120)

        # Create new instance pointing to same file
        reloaded = ConfigManager()
        self.assertEqual(reloaded.get("theme_mode"), "light")
        self.assertEqual(reloaded.get("sync_interval"), 120)

if __name__ == "__main__":
    unittest.main()

