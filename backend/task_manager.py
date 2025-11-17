"""
In-memory task storage with 24-hour auto-cleanup.
Manages analysis tasks and their results without database persistence.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configure logging for task tracking
logger = logging.getLogger(__name__)

# In-memory storage: {task_id: task_data}
_tasks: Dict[str, Dict[str, Any]] = {}


def create_task(sender_id: str, email_limit: int, batch_size: int) -> str:
    """
    Create a new analysis task and return its unique ID.

    Args:
        sender_id: Email sender identifier
        email_limit: Maximum number of emails to analyze
        batch_size: Number of emails per batch

    Returns:
        Unique task ID (UUID string)
    """
    task_id = str(uuid.uuid4())

    _tasks[task_id] = {
        "task_id": task_id,
        "sender_id": sender_id,
        "email_limit": email_limit,
        "batch_size": batch_size,
        "status": "processing",  # processing, completed, failed
        "progress": "0/0",
        "results": [],
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    logger.info(f"Task created: {task_id}")
    logger.debug(f"[{task_id}] Sender={sender_id}, limit={email_limit}, batch={batch_size}")

    return task_id


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve task data by ID.

    Args:
        task_id: Unique task identifier

    Returns:
        Task data dictionary or None if not found
    """
    task = _tasks.get(task_id)

    if task:
        # Return copy to prevent external modifications
        return task.copy()

    logger.warning(f"[{task_id}] Task not found")
    return None


def update_task(task_id: str, **updates) -> bool:
    """
    Update task data with provided fields.

    Args:
        task_id: Unique task identifier
        **updates: Key-value pairs to update

    Returns:
        True if updated, False if task not found
    """
    if task_id not in _tasks:
        logger.warning(f"[{task_id}] Cannot update - task not found")
        return False

    # Update specified fields
    for key, value in updates.items():
        _tasks[task_id][key] = value

    # Always update timestamp
    _tasks[task_id]["updated_at"] = datetime.now()

    logger.debug(f"[{task_id}] Updated: {', '.join(updates.keys())}")

    return True


def add_result(task_id: str, result: Dict[str, Any]) -> bool:
    """
    Append a result to task's results list.

    Args:
        task_id: Unique task identifier
        result: Result dictionary to append

    Returns:
        True if added, False if task not found
    """
    if task_id not in _tasks:
        logger.warning(f"[{task_id}] Cannot add result - task not found")
        return False

    _tasks[task_id]["results"].append(result)
    _tasks[task_id]["updated_at"] = datetime.now()

    logger.debug(f"[{task_id}] Added result (total: {len(_tasks[task_id]['results'])})")

    return True


def cleanup_old_tasks(hours: int = 24) -> int:
    """
    Remove tasks older than specified hours (default: 24).

    Args:
        hours: Age threshold in hours

    Returns:
        Number of tasks deleted
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    tasks_to_delete = []

    # Find old tasks
    for task_id, task_data in _tasks.items():
        if task_data["created_at"] < cutoff_time:
            tasks_to_delete.append(task_id)

    # Delete old tasks
    for task_id in tasks_to_delete:
        del _tasks[task_id]
        logger.debug(f"[{task_id}] Deleted - older than {hours} hours")

    if tasks_to_delete:
        logger.info(f"Cleanup complete: {len(tasks_to_delete)} tasks deleted")

    return len(tasks_to_delete)


def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Get all tasks (for debugging/monitoring).

    Returns:
        List of all task data dictionaries
    """
    return [task.copy() for task in _tasks.values()]
