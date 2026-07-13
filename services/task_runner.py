import threading
import asyncio
import logging
from typing import Dict, Any, Optional

class TaskLogCaptureHandler(logging.Handler):
    def __init__(self, task_name: str, registry):
        super().__init__()
        self.task_name = task_name
        self.registry = registry
        self.setLevel(logging.INFO)

    def emit(self, record):
        try:
            # We want only logs from app, nodes, graph, linkedin packages
            # to filter out third-party/library logs (like google, urllib3, etc.)
            if not any(pkg in record.name for pkg in ["nodes", "graph", "linkedin", "app"]):
                return
            
            clean_msg = record.getMessage()
            # Ignore some noisy/technical info messages if any remain
            if "Cache" in clean_msg or "database" in clean_msg.lower():
                return
                
            self.registry.update_progress(self.task_name, clean_msg)
        except Exception:
            self.handleError(record)

class TaskStatusRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def start_task(self, name: str, coro_func, *args, **kwargs) -> bool:
        """Starts a background task if not already running.
        
        Returns:
            bool: True if started, False if already running.
        """
        with self._lock:
            if name in self._tasks and self._tasks[name]["status"] == "running":
                return False

            self._tasks[name] = {
                "status": "running",
                "progress": "Initializing...",
                "error": None,
                "result": None
            }

        thread = threading.Thread(
            target=self._run_in_thread,
            args=(name, coro_func, args, kwargs),
            daemon=True
        )
        thread.start()
        return True

    def _run_in_thread(self, name: str, coro_func, args, kwargs):
        # Set up a new event loop for this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Attach the log capturer
        handler = TaskLogCaptureHandler(name, self)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        try:
            result = loop.run_until_complete(coro_func(*args, **kwargs))
            with self._lock:
                if name in self._tasks:
                    self._tasks[name]["status"] = "success"
                    self._tasks[name]["result"] = result
                    self._tasks[name]["progress"] = "Completed successfully."
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logging.getLogger("task_runner").error(f"Task {name} failed:\n{tb}")
            with self._lock:
                if name in self._tasks:
                    self._tasks[name]["status"] = "error"
                    self._tasks[name]["error"] = str(e)
                    self._tasks[name]["progress"] = f"Failed: {str(e)}"
        finally:
            # Clean up handler and loop
            try:
                root_logger.removeHandler(handler)
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass

    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._tasks.get(name)

    def update_progress(self, name: str, progress: str):
        with self._lock:
            if name in self._tasks and self._tasks[name]["status"] == "running":
                self._tasks[name]["progress"] = progress

    def clear_task(self, name: str):
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]

# Singleton instance
task_registry = TaskStatusRegistry()
