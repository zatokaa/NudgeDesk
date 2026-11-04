"""Data models for NudgeDesk."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class TaskList:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    remote_id: Optional[str] = None
    title: str = "My Tasks"
    updated: Optional[str] = None
    is_default: bool = False
    is_deleted: bool = False
    sync_status: str = "synced"

    @property
    def sync_id(self) -> str:
        """Returns remote_id if available, otherwise local id."""
        return self.remote_id or self.id

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    remote_id: Optional[str] = None
    list_id: str = "@default"
    title: str = ""
    notes: Optional[str] = ""
    status: str = "needsAction"  # "needsAction" or "completed"
    due: Optional[str] = None     # ISO formatted string: YYYY-MM-DD or RFC 3339
    completed_at: Optional[str] = None
    priority: int = 0            # 0=None, 1=Low, 2=Medium, 3=High
    position: Optional[str] = None
    parent: Optional[str] = None
    is_deleted: bool = False
    local_updated_at: str = field(default_factory=_utc_now_iso)
    remote_updated_at: Optional[str] = None
    sync_status: str = "synced"

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def sync_id(self) -> str:
        return self.remote_id or self.id

@dataclass
class SyncQueueItem:
    id: Optional[int] = None
    action: str = ""             # 'create', 'update', 'delete'
    entity_type: str = "task"    # 'task' or 'task_list'
    entity_id: str = ""          # local id
    remote_id: Optional[str] = None
    payload: str = "{}"          # JSON string
    created_at: str = field(default_factory=_utc_now_iso)
    retry_count: int = 0
    last_error: Optional[str] = None
