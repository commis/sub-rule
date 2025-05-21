import threading
import time
from uuid import uuid4

from core.core_singleton import singleton


@singleton
class TaskManager:
    def __init__(self):
        self.__tasks = {}
        self.__lock = threading.RLock()

    def create_task(self, **kwargs):
        task_id = str(uuid4()).replace('-', '')
        task = {
            "id": task_id,
            "type": kwargs['type'],
            "status": "initializing",
            "description": kwargs['description'],
            'url': kwargs['url'],
            "progress": 0,
            "processed": 0,
            "total": 0,
            "success": 0,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "result": None,
            "error": None
        }

        with self.__lock:
            self.__tasks[task_id] = task
            task["status"] = "pending"

        return task_id

    def get_tasks(self):
        with self.__lock:
            return [{"id": task["id"], "status": task["status"]} for task in self.__tasks.values()]

    def get_task(self, task_id):
        with self.__lock:
            return self.__tasks.get(task_id)

    def update_task(self, task_id, **kwargs):
        with self.__lock:
            if task_id not in self.__tasks:
                return False

            if 'status' in kwargs and kwargs['status'] not in {'pending', 'running', 'completed', 'failed'}:
                return False

            task = self.__tasks[task_id]
            task.update(kwargs)
            task["updated_at"] = int(time.time())
            return True

    def delete_task(self, task_id):
        with self.__lock:
            task = self.__tasks.get(task_id)
            if not task:
                return False

            if task["status"] not in {"completed", "failed"}:
                return False

            return self.__tasks.pop(task_id, None) is not None

    def safe_get_and_update_task(self, task_id, update_func):
        with self.__lock:
            task = self.__tasks.get(task_id)
            if not task:
                return False

            update_func(task)
            task["updated_at"] = int(time.time())
            return True
