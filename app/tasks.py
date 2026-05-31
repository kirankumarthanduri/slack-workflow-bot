import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Simple file-based task storage
# Saves tasks to tasks.json — no database needed
# ─────────────────────────────────────────────

TASKS_FILE = "tasks.json"


def load_tasks():
    """Load all tasks from the JSON file."""
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return []


def save_tasks(tasks):
    """Save all tasks to the JSON file."""
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving tasks: {e}")


def add_task(assigned_to, description, assigned_by, due_date=None):
    """Add a new task and return it."""
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "assigned_to": assigned_to,       # Slack user ID
        "description": description,
        "assigned_by": assigned_by,        # Slack user ID
        "due_date": due_date,              # e.g. "Friday" or "2024-12-20"
        "status": "open",                  # open / done
        "created_at": datetime.now().isoformat(),
        "nudge_count": 0,                  # how many times we've nudged
        "last_nudged": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    logger.info(f"Task #{task['id']} added: {description} → {assigned_to}")
    return task


def get_open_tasks():
    """Return all tasks with status 'open'."""
    return [t for t in load_tasks() if t.get("status") == "open"]


def get_tasks_for_user(user_id):
    """Return all open tasks assigned to a specific user."""
    return [t for t in load_tasks()
            if t.get("assigned_to") == user_id and t.get("status") == "open"]


def complete_task(task_id):
    """Mark a task as done. Returns the task or None if not found."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "done"
            task["completed_at"] = datetime.now().isoformat()
            save_tasks(tasks)
            logger.info(f"Task #{task_id} marked as done")
            return task
    return None


def update_nudge(task_id):
    """Increment nudge count and update last nudged time."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["nudge_count"] = task.get("nudge_count", 0) + 1
            task["last_nudged"] = datetime.now().isoformat()
            save_tasks(tasks)
            return task
    return None


def get_tasks_needing_nudge(max_nudges=3):
    """
    Return open tasks that haven't been nudged recently.
    Limits to max_nudges total nudges per task to avoid spam.
    """
    tasks = get_open_tasks()
    to_nudge = []
    for task in tasks:
        nudge_count = task.get("nudge_count", 0)
        if nudge_count < max_nudges:
            to_nudge.append(task)
    return to_nudge
