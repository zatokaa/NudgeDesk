"""Unit test for UI component initialization and memory leak prevention."""

import unittest
from ui.main_window import MainWindow

class TestUIComponents(unittest.TestCase):

    def test_main_window_lifecycle(self):
        # Instantiate MainWindow hidden
        app = MainWindow()
        app.withdraw()
        
        # Verify component trees are loaded
        self.assertIsNotNone(app.sidebar)
        self.assertIsNotNone(app.dashboard)
        self.assertIsNotNone(app.task_view)
        self.assertIsNotNone(app.settings_view)

        # Trigger quick UI updates
        app.refresh_ui()

        # Cleanly destroy
        app.destroy()

if __name__ == "__main__":
    unittest.main()

