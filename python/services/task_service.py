import threading
import time
from uuid import uuid4

from core.core_singleton import singleton


@singleton
class TaskService:
    def __init__(self):
        self.__tasks = {}
        self.__lock = threading.Lock()

    def create_task(self, task_type, description=""):
        task_id = str(uuid4()).replace('-', '')
        task = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "description": description,
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

        return task_id

    def get_task(self, task_id):
        with self.__lock:
            return self.__tasks.get(task_id)

    def update_task(self, task_id, **kwargs):
        with self.__lock:
            if task_id in self.__tasks:
                self.__tasks[task_id].update(kwargs)
                self.__tasks[task_id]["updated_at"] = int(time.time())
                return True
        return False

    def delete_task(self, task_id):
        with self.__lock:
            if task_id in self.__tasks:
                del self.__tasks[task_id]
                return True
        return False
