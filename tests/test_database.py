"""Unit tests for SQLite database manager and data models."""

import unittest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import os

from database.models import Task, TaskList, SyncQueueItem
from database.db_manager import DatabaseManager
from config.constants import STATUS_SYNCED, STATUS_PENDING

class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tasks.db"
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_task_list_crud(self):
        t_list = TaskList(title="Work Tasks", is_default=True)
        self.db.upsert_list(t_list)

        fetched = self.db.get_list_by_id(t_list.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Work Tasks")
        self.assertTrue(fetched.is_default)

        # Update title
        t_list.title = "Work & Projects"
        self.db.upsert_list(t_list)
        updated = self.db.get_list_by_id(t_list.id)
        self.assertEqual(updated.title, "Work & Projects")

    def test_task_crud_and_filters(self):
        today_str = date.today().isoformat()
        tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        # Task 1: Due today
        t1 = Task(title="Today Urgent Task", due=today_str, list_id="@default")
        # Task 2: Due tomorrow (Upcoming)
        t2 = Task(title="Future Project Task", due=tomorrow_str, list_id="@default")
        # Task 3: Overdue
        t3 = Task(title="Past Overdue Task", due=yesterday_str, list_id="@default")
        # Task 4: Completed
        t4 = Task(title="Finished Task", status="completed", due=today_str, list_id="@default")

        for t in [t1, t2, t3, t4]:
            self.db.upsert_task(t)

        # Test My Day filter (includes today and overdue tasks that need action)
        my_day_tasks = self.db.get_tasks(filter_type="my_day")
        my_day_titles = [t.title for t in my_day_tasks]
        self.assertIn("Today Urgent Task", my_day_titles)
        self.assertIn("Past Overdue Task", my_day_titles)
        self.assertNotIn("Future Project Task", my_day_titles)
        self.assertNotIn("Finished Task", my_day_titles)

        # Test Upcoming filter
        upcoming_tasks = self.db.get_tasks(filter_type="upcoming")
        upcoming_titles = [t.title for t in upcoming_tasks]
        self.assertIn("Future Project Task", upcoming_titles)
        self.assertNotIn("Today Urgent Task", upcoming_titles)

        # Test Completed filter
        completed_tasks = self.db.get_tasks(filter_type="completed")
        completed_titles = [t.title for t in completed_tasks]
        self.assertIn("Finished Task", completed_titles)
        self.assertNotIn("Today Urgent Task", completed_titles)

        # Test Search filter
        search_res = self.db.get_tasks(search="Urgent")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].title, "Today Urgent Task")

        # Test Metrics Counts
        counts = self.db.get_dashboard_counts()
        self.assertEqual(counts["today"], 2)  # today + overdue
        self.assertEqual(counts["upcoming"], 1)
        self.assertEqual(counts["completed"], 1)
        self.assertEqual(counts["pending"], 3)

    def test_sync_queue(self):
        # Enqueue item
        qid = self.db.enqueue_sync(
            action="create_task",
            entity_type="task",
            entity_id="local-uuid-123",
            payload={"title": "Sync Me"}
        )
        self.assertIsNotNone(qid)

        items = self.db.get_pending_sync_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].action, "create_task")
        self.assertEqual(items[0].entity_id, "local-uuid-123")

        # Remove item after successful sync
        self.db.remove_sync_item(qid)
        items_after = self.db.get_pending_sync_items()
        self.assertEqual(len(items_after), 0)

if __name__ == "__main__":
    unittest.main()
