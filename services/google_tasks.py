"""Google Tasks API v1 integration service."""

import time
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.google_auth import google_auth
from utils.logger import logger

class GoogleTasksService:
    """Wrapper for Google Tasks REST API v1 operations."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        creds = google_auth.get_valid_credentials()
        if not creds:
            return None
        # Lightweight service construction with cache_discovery=False to prevent disk cache issues
        if self._service is None or self._service._http.credentials != creds:
            self._service = build("tasks", "v1", credentials=creds, cache_discovery=False)
        return self._service

    def is_ready(self) -> bool:
        return self._get_service() is not None

    def fetch_task_lists(self) -> List[Dict[str, Any]]:
        """Retrieves all Google Task lists for the authenticated user."""
        service = self._get_service()
        if not service:
            return []

        try:
            lists = []
            page_token = None
            while True:
                req = service.tasklists().list(maxResults=100, pageToken=page_token)
                res = req.execute()
                items = res.get("items", [])
                lists.extend(items)
                page_token = res.get("nextPageToken")
                if not page_token:
                    break
            return lists
        except HttpError as e:
            logger.error(f"Google Tasks API error while fetching lists: {e}")
            raise

    def fetch_tasks(self, list_id: str = "@default", show_completed: bool = True, show_hidden: bool = True) -> List[Dict[str, Any]]:
        """Retrieves all tasks for a specific task list."""
        service = self._get_service()
        if not service:
            return []

        try:
            tasks = []
            page_token = None
            while True:
                req = service.tasks().list(
                    tasklist=list_id,
                    maxResults=100,
                    showCompleted=show_completed,
                    showHidden=show_hidden,
                    pageToken=page_token
                )
                res = req.execute()
                items = res.get("items", [])
                tasks.extend(items)
                page_token = res.get("nextPageToken")
                if not page_token:
                    break
            return tasks
        except HttpError as e:
            logger.error(f"Google Tasks API error while fetching tasks for list {list_id}: {e}")
            raise

    def create_task(self, list_id: str, title: str, notes: Optional[str] = None, due: Optional[str] = None) -> Dict[str, Any]:
        """Creates a new task in Google Tasks."""
        service = self._get_service()
        if not service:
            raise RuntimeError("Not authenticated with Google Tasks.")

        body: Dict[str, Any] = {"title": title}
        if notes:
            body["notes"] = notes
        if due:
            # Google Tasks API expects RFC 3339 formatted timestamp, e.g. 2026-11-01T00:00:00.000Z
            if len(due) == 10:
                body["due"] = f"{due}T00:00:00.000Z"
            else:
                body["due"] = due

        return service.tasks().insert(tasklist=list_id, body=body).execute()

    def update_task(self, list_id: str, task_id: str, title: Optional[str] = None, notes: Optional[str] = None, due: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Updates an existing task in Google Tasks."""
        service = self._get_service()
        if not service:
            raise RuntimeError("Not authenticated with Google Tasks.")

        body: Dict[str, Any] = {"id": task_id}
        if title is not None:
            body["title"] = title
        if notes is not None:
            body["notes"] = notes
        if due is not None:
            if due:
                if len(due) == 10:
                    body["due"] = f"{due}T00:00:00.000Z"
                else:
                    body["due"] = due
            else:
                body["due"] = None
        if status is not None:
            body["status"] = status

        return service.tasks().patch(tasklist=list_id, task=task_id, body=body).execute()

    def delete_task(self, list_id: str, task_id: str) -> bool:
        """Deletes a task from Google Tasks."""
        service = self._get_service()
        if not service:
            raise RuntimeError("Not authenticated with Google Tasks.")

        try:
            service.tasks().delete(tasklist=list_id, task=task_id).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                logger.info(f"Task {task_id} already deleted remotely.")
                return True
            raise

    def create_task_list(self, title: str) -> Dict[str, Any]:
        """Creates a new Task List in Google Tasks."""
        service = self._get_service()
        if not service:
            raise RuntimeError("Not authenticated with Google Tasks.")

        return service.tasklists().insert(body={"title": title}).execute()

    def delete_task_list(self, list_id: str) -> bool:
        """Deletes a Task List from Google Tasks."""
        service = self._get_service()
        if not service:
            raise RuntimeError("Not authenticated with Google Tasks.")

        try:
            service.tasklists().delete(tasklist=list_id).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return True
            raise

google_tasks_api = GoogleTasksService()

