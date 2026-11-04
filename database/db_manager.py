"""SQLite Database Manager for NudgeDesk."""

import sqlite3
import json
import threading
from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from contextlib import contextmanager
from database.models import TaskList, Task, SyncQueueItem
from config.constants import DATABASE_PATH, STATUS_PENDING, STATUS_SYNCED
from utils.logger import logger

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DatabaseManager:
    """Thread-safe SQLite manager for caching, offline tasks, and sync queue."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._lock = threading.RLock()
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Yields a connection configured with Row factory and WAL mode, closing it after use."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Creates tables, indices and triggers if not present."""
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Task Lists Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_lists (
                id TEXT PRIMARY KEY,
                remote_id TEXT UNIQUE,
                title TEXT NOT NULL,
                updated TEXT,
                is_default INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'synced'
            )
            """)

            # Tasks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                remote_id TEXT UNIQUE,
                list_id TEXT NOT NULL,
                title TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'needsAction',
                due TEXT,
                completed_at TEXT,
                priority INTEGER DEFAULT 0,
                position TEXT,
                parent TEXT,
                is_deleted INTEGER DEFAULT 0,
                local_updated_at TEXT NOT NULL,
                remote_updated_at TEXT,
                sync_status TEXT DEFAULT 'synced'
            )
            """)

            # Sync Queue Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                remote_id TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                last_error TEXT
            )
            """)

            # Indices for rapid querying & low CPU
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_list ON tasks(list_id, is_deleted)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, is_deleted)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_remote ON tasks(remote_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_created ON sync_queue(created_at)")

            conn.commit()
            logger.info("SQLite database initialized successfully.")

    # =========================================================================
    # Task List Methods
    # =========================================================================

    def get_all_lists(self, include_deleted: bool = False) -> List[TaskList]:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM task_lists"
            if not include_deleted:
                query += " WHERE is_deleted = 0"
            query += " ORDER BY is_default DESC, title ASC"
            rows = cursor.execute(query).fetchall()
            return [
                TaskList(
                    id=r["id"],
                    remote_id=r["remote_id"],
                    title=r["title"],
                    updated=r["updated"],
                    is_default=bool(r["is_default"]),
                    is_deleted=bool(r["is_deleted"]),
                    sync_status=r["sync_status"],
                )
                for r in rows
            ]

    def get_list_by_id(self, list_id: str) -> Optional[TaskList]:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM task_lists WHERE (id = ? OR remote_id = ?) AND is_deleted = 0",
                (list_id, list_id)
            ).fetchone()
            if row:
                return TaskList(
                    id=row["id"],
                    remote_id=row["remote_id"],
                    title=row["title"],
                    updated=row["updated"],
                    is_default=bool(row["is_default"]),
                    is_deleted=bool(row["is_deleted"]),
                    sync_status=row["sync_status"],
                )
            return None

    def get_default_list(self) -> Optional[TaskList]:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM task_lists WHERE is_default = 1 AND is_deleted = 0"
            ).fetchone()
            if not row:
                row = cursor.execute(
                    "SELECT * FROM task_lists WHERE is_deleted = 0 ORDER BY rowid ASC LIMIT 1"
                ).fetchone()
            if row:
                return TaskList(
                    id=row["id"],
                    remote_id=row["remote_id"],
                    title=row["title"],
                    updated=row["updated"],
                    is_default=bool(row["is_default"]),
                    is_deleted=bool(row["is_deleted"]),
                    sync_status=row["sync_status"],
                )
            return None

    def upsert_list(self, task_list: TaskList) -> None:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO task_lists (id, remote_id, title, updated, is_default, is_deleted, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                remote_id = coalesce(excluded.remote_id, task_lists.remote_id),
                title = excluded.title,
                updated = excluded.updated,
                is_default = excluded.is_default,
                is_deleted = excluded.is_deleted,
                sync_status = excluded.sync_status
            """, (
                task_list.id,
                task_list.remote_id,
                task_list.title,
                task_list.updated,
                1 if task_list.is_default else 0,
                1 if task_list.is_deleted else 0,
                task_list.sync_status
            ))
            conn.commit()

    # =========================================================================
    # Task Methods
    # =========================================================================

    def _row_to_task(self, r: sqlite3.Row) -> Task:
        return Task(
            id=r["id"],
            remote_id=r["remote_id"],
            list_id=r["list_id"],
            title=r["title"],
            notes=r["notes"] or "",
            status=r["status"],
            due=r["due"],
            completed_at=r["completed_at"],
            priority=r["priority"] or 0,
            position=r["position"],
            parent=r["parent"],
            is_deleted=bool(r["is_deleted"]),
            local_updated_at=r["local_updated_at"],
            remote_updated_at=r["remote_updated_at"],
            sync_status=r["sync_status"],
        )

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM tasks WHERE id = ? OR remote_id = ?",
                (task_id, task_id)
            ).fetchone()
            if row:
                return self._row_to_task(row)
            return None

    def get_tasks(self, filter_type: str = "all", list_id: Optional[str] = None, search: str = "") -> List[Task]:
        """Flexible query for My Day, All, Upcoming, Completed, and custom list views."""
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            today_str = date.today().isoformat()
            
            query = "SELECT * FROM tasks WHERE is_deleted = 0"
            params: List[Any] = []

            if search:
                query += " AND (title LIKE ? OR notes LIKE ?)"
                like_term = f"%{search.strip()}%"
                params.extend([like_term, like_term])

            if filter_type == "my_day":
                # Due today or overdue and not completed
                query += " AND status = 'needsAction' AND due IS NOT NULL AND substr(due, 1, 10) <= ?"
                params.append(today_str)
            elif filter_type == "upcoming":
                # Due in the future and not completed
                query += " AND status = 'needsAction' AND due IS NOT NULL AND substr(due, 1, 10) > ?"
                params.append(today_str)
            elif filter_type == "completed":
                query += " AND status = 'completed'"
            elif filter_type == "list" and list_id:
                query += " AND (list_id = ? OR list_id IN (SELECT id FROM task_lists WHERE remote_id = ?))"
                params.extend([list_id, list_id])

            # Order: Completed at bottom, then priority high to low, then due date ascending, then local update
            query += """
            ORDER BY 
                CASE WHEN status = 'completed' THEN 1 ELSE 0 END ASC,
                priority DESC,
                CASE WHEN due IS NULL OR due = '' THEN '9999-99-99' ELSE due END ASC,
                local_updated_at DESC
            """
            rows = cursor.execute(query, params).fetchall()
            return [self._row_to_task(r) for r in rows]

    def upsert_task(self, task: Task) -> None:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO tasks (
                id, remote_id, list_id, title, notes, status, due,
                completed_at, priority, position, parent, is_deleted,
                local_updated_at, remote_updated_at, sync_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                remote_id = coalesce(excluded.remote_id, tasks.remote_id),
                list_id = excluded.list_id,
                title = excluded.title,
                notes = excluded.notes,
                status = excluded.status,
                due = excluded.due,
                completed_at = excluded.completed_at,
                priority = excluded.priority,
                position = excluded.position,
                parent = excluded.parent,
                is_deleted = excluded.is_deleted,
                local_updated_at = excluded.local_updated_at,
                remote_updated_at = excluded.remote_updated_at,
                sync_status = excluded.sync_status
            """, (
                task.id,
                task.remote_id,
                task.list_id,
                task.title,
                task.notes,
                task.status,
                task.due,
                task.completed_at,
                task.priority,
                task.position,
                task.parent,
                1 if task.is_deleted else 0,
                task.local_updated_at,
                task.remote_updated_at,
                task.sync_status
            ))
            conn.commit()

    def mark_task_deleted(self, task_id: str) -> None:
        """Marks task as deleted and queues sync operation."""
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = _utc_now_iso()
            cursor.execute(
                "UPDATE tasks SET is_deleted = 1, local_updated_at = ?, sync_status = 'pending' WHERE id = ? OR remote_id = ?",
                (now_iso, task_id, task_id)
            )
            conn.commit()

    def get_dashboard_counts(self) -> Dict[str, int]:
        """Returns statistics for Bento Box cards."""
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            today_str = date.today().isoformat()

            # Today's tasks (due today or overdue and pending)
            today_count = cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE is_deleted = 0 AND status = 'needsAction' AND due IS NOT NULL AND substr(due, 1, 10) <= ?
            """, (today_str,)).fetchone()[0]

            # Upcoming tasks (future due date and pending)
            upcoming_count = cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE is_deleted = 0 AND status = 'needsAction' AND due IS NOT NULL AND substr(due, 1, 10) > ?
            """, (today_str,)).fetchone()[0]

            # Completed tasks
            completed_count = cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE is_deleted = 0 AND status = 'completed'
            """).fetchone()[0]

            # Total pending tasks
            pending_count = cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE is_deleted = 0 AND status = 'needsAction'
            """).fetchone()[0]

            return {
                "today": today_count,
                "upcoming": upcoming_count,
                "completed": completed_count,
                "pending": pending_count,
            }

    # =========================================================================
    # Synchronization Queue Methods
    # =========================================================================

    def enqueue_sync(self, action: str, entity_type: str, entity_id: str, remote_id: Optional[str] = None, payload: Dict[str, Any] = None) -> int:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            payload_str = json.dumps(payload or {})
            now_iso = _utc_now_iso()
            cursor.execute("""
            INSERT INTO sync_queue (action, entity_type, entity_id, remote_id, payload, created_at, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (action, entity_type, entity_id, remote_id, payload_str, now_iso))
            conn.commit()
            return cursor.lastrowid

    def get_pending_sync_items(self, limit: int = 50) -> List[SyncQueueItem]:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT * FROM sync_queue ORDER BY id ASC LIMIT ?
            """, (limit,)).fetchall()
            return [
                SyncQueueItem(
                    id=r["id"],
                    action=r["action"],
                    entity_type=r["entity_type"],
                    entity_id=r["entity_id"],
                    remote_id=r["remote_id"],
                    payload=r["payload"],
                    created_at=r["created_at"],
                    retry_count=r["retry_count"],
                    last_error=r["last_error"],
                )
                for r in rows
            ]

    def remove_sync_item(self, item_id: int) -> None:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
            conn.commit()

    def increment_sync_retry(self, item_id: int, error_msg: str) -> None:
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE sync_queue 
            SET retry_count = retry_count + 1, last_error = ?
            WHERE id = ?
            """, (error_msg, item_id))
            conn.commit()

    def clear_all_data(self) -> None:
        """Cleans all local cached tables (e.g. on cache clear / account disconnect)."""
        with self._lock, self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_queue")
            cursor.execute("DELETE FROM tasks")
            cursor.execute("DELETE FROM task_lists")
            conn.commit()
            logger.info("Cleared all local database tables.")

db = DatabaseManager()
