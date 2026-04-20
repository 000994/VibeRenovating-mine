import asyncio
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from core.generator import GenerationTask, Generator
from models.database import Database
from utils.storage import StorageManager


_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _set_job_state(task_id: str, **updates: Any) -> None:
    with _jobs_lock:
        state = _jobs.get(task_id, {"task_id": task_id})
        state.update(updates)
        _jobs[task_id] = state


def start_generation_task(
    task: GenerationTask,
    api_keys: Dict[Any, Dict[str, Any]],
    generation_options: Optional[Dict[str, Any]] = None,
) -> bool:
    generation_options = generation_options or {}

    with _jobs_lock:
        existing = _jobs.get(task.task_id)
        if existing and existing.get("status") == "running":
            return False

        _jobs[task.task_id] = {
            "task_id": task.task_id,
            "status": "running",
            "provider": task.provider.value,
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "error": None,
            "result": None,
        }

    def _worker() -> None:
        worker_db = Database()
        worker_generator = Generator(db=worker_db, storage=StorageManager())
        try:
            result = asyncio.run(
                worker_generator.execute_task(task, api_keys, generation_options=generation_options)
            )
            _set_job_state(
                task.task_id,
                status="completed",
                finished_at=datetime.utcnow().isoformat(),
                result={
                    "status": result.status.value,
                    "error_message": result.error_message,
                    "model_url": result.model_url,
                    "preview_url": result.preview_url,
                    "job_id": result.job_id,
                },
            )
        except Exception as exc:
            _set_job_state(
                task.task_id,
                status="failed",
                finished_at=datetime.utcnow().isoformat(),
                error=str(exc),
            )

    thread = threading.Thread(target=_worker, name=f"gen-{task.task_id[:8]}", daemon=True)
    thread.start()
    return True


def get_generation_task_state(task_id: str) -> Optional[Dict[str, Any]]:
    with _jobs_lock:
        state = _jobs.get(task_id)
        return dict(state) if state else None


def list_running_task_ids() -> list[str]:
    with _jobs_lock:
        return [task_id for task_id, state in _jobs.items() if state.get("status") == "running"]
