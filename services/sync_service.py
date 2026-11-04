"""Background Synchronization Service for Google Tasks and SQLite Cache."""

import time
import json
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from database.db_manager import db
from database.models import Task, TaskList, SyncQueueItem
from services.google_auth import google_auth
from services.google_tasks import google_tasks_api
from utils.config_manager import config_manager
from utils.logger import logger
from config.constants import (
    STATUS_SYNCED,
    STATUS_SYNCING,
    STATUS_OFFLINE,
    STATUS_PENDING,
    STATUS_ERROR,
    DEFAULT_SYNC_INTERVAL_SECONDS,
)
from utils.memory_optimizer import trim_memory

class SyncService:
    """Coordinates two-way background synchronization between Google Tasks and local SQLite."""

    def __init__(self):
        self._sync_lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._trigger_event = threading.Event()
        
        self.current_status: str = STATUS_SYNCED
        self.last_sync_time: Optional[datetime] = None
        self.last_error_message: Optional[str] = None
        
        # UI callback hooks (executed safely on UI thread via root.after or direct callback)
        self.on_status_change: Optional[Callable[[str, Optional[str]], None]] = None
        self.on_sync_completed: Optional[Callable[[], None]] = None

    def start(self) -> None:
        """Starts the background synchronization loop."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._run_loop,
            name="NudgeDesk-SyncWorker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info("Background synchronization worker started.")

    def stop(self) -> None:
        """Signals the sync thread to terminate gracefully."""
        self._stop_event.set()
        self._trigger_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        logger.info("Background synchronization worker stopped.")

    def trigger_sync(self) -> None:
        """Triggers an immediate sync cycle in the background worker."""
        self._trigger_event.set()

    def set_status(self, status: str, message: Optional[str] = None) -> None:
        self.current_status = status
        if message:
            self.last_error_message = message
        if self.on_status_change:
            try:
                self.on_status_change(status, message)
            except Exception as e:
                logger.error(f"Error in on_status_change callback: {e}")

    def _run_loop(self) -> None:
        """Main loop of the background synchronization thread."""
        # Initial sync on launch after short pause
        time.sleep(1.5)
        self.trigger_sync()

        while not self._stop_event.is_set():
            interval = config_manager.get("sync_interval", DEFAULT_SYNC_INTERVAL_SECONDS)
            auto_sync = config_manager.get("auto_sync", True)
            
            # Wait for either the configured interval or manual trigger event
            triggered = self._trigger_event.wait(timeout=interval if auto_sync else 3600)
            if self._stop_event.is_set():
                break

            if triggered:
                self._trigger_event.clear()

            if auto_sync or triggered:
                self._perform_sync()

    def _perform_sync(self) -> None:
        """Executes one full sync pass with lock to avoid concurrent runs."""
        if not self._sync_lock.acquire(blocking=False):
            logger.debug("Sync cycle already in progress, skipping duplicate trigger.")
            return

        try:
            if not google_auth.is_authenticated():
                self.set_status(STATUS_OFFLINE, "Not signed in to Google.")
                return

            self.set_status(STATUS_SYNCING, "Synchronizing with Google Tasks...")
            logger.info("Starting synchronization cycle...")

            # Step 1: Process local pending offline queue first
            self._process_sync_queue()

            # Step 2: Fetch remote task lists
            remote_lists = google_tasks_api.fetch_task_lists()
            self._reconcile_task_lists(remote_lists)

            # Step 3: Fetch tasks for each list and reconcile
            for r_list in remote_lists:
                list_id = r_list["id"]
                remote_tasks = google_tasks_api.fetch_tasks(list_id)
                self._reconcile_tasks(list_id, remote_tasks)

            self.last_sync_time = datetime.now()
            config_manager.set("last_sync_timestamp", self.last_sync_time.isoformat())
            self.set_status(STATUS_SYNCED, "All tasks up to date.")
            logger.info("Synchronization completed successfully.")

            if self.on_sync_completed:
                try:
                    self.on_sync_completed()
                except Exception as e:
                    logger.error(f"Error in on_sync_completed callback: {e}")

        except Exception as e:
            err_msg = str(e)
            if "Google Tasks API has not been used in project" in err_msg or "accessNotConfigured" in err_msg:
                user_msg = "Google Tasks API is not enabled in your Google Cloud Project. Please enable it in Google Cloud Console."
            else:
                user_msg = f"Sync error: {err_msg}"
            logger.error(f"Synchronization error: {err_msg}", exc_info=True)
            self.set_status(STATUS_ERROR, user_msg)
        finally:
            self._sync_lock.release()
            trim_memory()

    # =========================================================================
    # Queue Processing
    # =========================================================================

    def _process_sync_queue(self) -> None:
        """Pushes locally modified/created/deleted items to Google Tasks."""
        pending_items = db.get_pending_sync_items()
        if not pending_items:
            return

        logger.info(f"Processing {len(pending_items)} pending offline actions from queue...")

        for item in pending_items:
            try:
                payload = json.loads(item.payload)
                if item.action == "create_task":
                    list_id = payload.get("list_id", "@default")
                    title = payload.get("title", "")
                    notes = payload.get("notes")
                    due = payload.get("due")
                    res = google_tasks_api.create_task(list_id, title, notes, due)
                    
                    # Update local task with remote id and synced status
                    task = db.get_task_by_id(item.entity_id)
                    if task:
                        task.remote_id = res["id"]
                        task.remote_updated_at = res.get("updated")
                        task.sync_status = STATUS_SYNCED
                        db.upsert_task(task)
                    db.remove_sync_item(item.id)

                elif item.action == "update_task":
                    list_id = payload.get("list_id", "@default")
                    task_id = item.remote_id or item.entity_id
                    res = google_tasks_api.update_task(
                        list_id=list_id,
                        task_id=task_id,
                        title=payload.get("title"),
                        notes=payload.get("notes"),
                        due=payload.get("due"),
                        status=payload.get("status")
                    )
                    task = db.get_task_by_id(item.entity_id)
                    if task:
                        task.remote_updated_at = res.get("updated")
                        task.sync_status = STATUS_SYNCED
                        db.upsert_task(task)
                    db.remove_sync_item(item.id)

                elif item.action == "delete_task":
                    list_id = payload.get("list_id", "@default")
                    task_id = item.remote_id or item.entity_id
                    if task_id:
                        google_tasks_api.delete_task(list_id, task_id)
                    db.remove_sync_item(item.id)

                elif item.action == "create_list":
                    title = payload.get("title", "New List")
                    res = google_tasks_api.create_task_list(title)
                    t_list = db.get_list_by_id(item.entity_id)
                    if t_list:
                        t_list.remote_id = res["id"]
                        t_list.sync_status = STATUS_SYNCED
                        db.upsert_list(t_list)
                    db.remove_sync_item(item.id)

            except Exception as e:
                logger.error(f"Failed to process sync queue item {item.id} ({item.action}): {e}")
                db.increment_sync_retry(item.id, str(e))
                # Break to avoid repeating failed queue in this round
                break

    # =========================================================================
    # Remote Reconciliation
    # =========================================================================

    def _reconcile_task_lists(self, remote_lists: List[Dict[str, Any]]) -> None:
        """Upserts task lists from Google Tasks into SQLite cache."""
        for idx, r_list in enumerate(remote_lists):
            r_id = r_list["id"]
            title = r_list.get("title", "Untitled List")
            updated = r_list.get("updated")
            
            existing = db.get_list_by_id(r_id)
            if existing:
                existing.remote_id = r_id
                existing.title = title
                existing.updated = updated
                existing.is_default = (idx == 0)
                existing.sync_status = STATUS_SYNCED
                db.upsert_list(existing)
            else:
                new_list = TaskList(
                    id=r_id,
                    remote_id=r_id,
                    title=title,
                    updated=updated,
                    is_default=(idx == 0),
                    sync_status=STATUS_SYNCED
                )
                db.upsert_list(new_list)

    def _reconcile_tasks(self, list_id: str, remote_tasks: List[Dict[str, Any]]) -> None:
        """Reconciles remote tasks with local cache, respecting conflict rules."""
        remote_task_ids = set()

        for r_task in remote_tasks:
            r_id = r_task["id"]
            remote_task_ids.add(r_id)
            title = r_task.get("title", "")
            notes = r_task.get("notes", "")
            status = r_task.get("status", "needsAction")
            due = r_task.get("due")
            completed_at = r_task.get("completed")
            position = r_task.get("position")
            parent = r_task.get("parent")
            remote_updated = r_task.get("updated")
            is_deleted = bool(r_task.get("deleted", False))

            # Format due date to YYYY-MM-DD for local display / comparison if present
            clean_due = due[:10] if due and len(due) >= 10 else due

            local_task = db.get_task_by_id(r_id)
            if local_task:
                # If local task has pending changes in sync queue, don't blindly overwrite
                if local_task.sync_status == STATUS_PENDING:
                    logger.debug(f"Task {r_id} has pending local changes, keeping local version for sync.")
                    continue

                # Update local task with remote values
                local_task.remote_id = r_id
                local_task.list_id = list_id
                local_task.title = title
                local_task.notes = notes
                local_task.status = status
                local_task.due = clean_due
                local_task.completed_at = completed_at
                local_task.position = position
                local_task.parent = parent
                local_task.is_deleted = is_deleted
                local_task.remote_updated_at = remote_updated
                local_task.sync_status = STATUS_SYNCED
                db.upsert_task(local_task)
            else:
                if not is_deleted:
                    new_task = Task(
                        id=r_id,
                        remote_id=r_id,
                        list_id=list_id,
                        title=title,
                        notes=notes,
                        status=status,
                        due=clean_due,
                        completed_at=completed_at,
                        priority=0,
                        position=position,
                        parent=parent,
                        is_deleted=False,
                        remote_updated_at=remote_updated,
                        sync_status=STATUS_SYNCED
                    )
                    db.upsert_task(new_task)

sync_service = SyncService()

