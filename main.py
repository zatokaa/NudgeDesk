"""NudgeDesk – Lightweight Google Tasks Desktop Companion for Windows 11.

Entry point for the application.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.single_instance import SingleInstanceChecker
from utils.logger import logger
from utils.config_manager import config_manager
from database.db_manager import db
from database.models import TaskList
from services.tray_service import tray_service
from services.sync_service import sync_service
from ui.main_window import MainWindow

def seed_initial_data_if_needed() -> None:
    """Creates a default 'My Tasks' list if database is empty."""
    lists = db.get_all_lists()
    if not lists:
        default_list = TaskList(
            id="@default",
            remote_id=None,
            title="My Tasks",
            is_default=True,
            sync_status="synced"
        )
        db.upsert_list(default_list)
        logger.info("Seeded default 'My Tasks' list.")

def parse_args():
    parser = argparse.ArgumentParser(description="NudgeDesk – Google Tasks Desktop Companion")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to the Windows system tray")
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. Single Instance Protection
    single_instance = SingleInstanceChecker("Local\\NudgeDesk_SingleInstance_Mutex")
    if single_instance.is_running():
        logger.info("NudgeDesk is already running. Activating existing window...")
        single_instance.activate_existing_window()
        sys.exit(0)

    try:
        # 2. Seed database default if fresh setup
        seed_initial_data_if_needed()

        # 3. Create Main UI Window
        app = MainWindow()

        # 4. Start Background Services
        sync_service.start()
        tray_service.start()

        # 5. Handle Minimized launch flag
        launch_minimized = args.minimized or config_manager.get("launch_minimized", False)
        if launch_minimized:
            app.withdraw()
            logger.info("Started minimized in system tray.")
        else:
            app.deiconify()

        # 6. Main Event Loop
        app.mainloop()

    finally:
        # Clean shutdown
        logger.info("Shutting down NudgeDesk...")
        sync_service.stop()
        tray_service.stop()
        single_instance.release()
        logger.info("NudgeDesk terminated gracefully.")

if __name__ == "__main__":
    main()

