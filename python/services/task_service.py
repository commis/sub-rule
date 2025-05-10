import threading
import time
from uuid import uuid4


class TaskService:
    __instance = None
    __lock = threading.Lock()

    @staticmethod
    def get_instance():
        with TaskService.__lock:
            if not TaskService.__instance:
                TaskService.__instance = TaskService()
            return TaskService.__instance

    def __init__(self):
        self.__tasks = {}
        self.__lock = threading.Lock()

    def create_task(self, task_type, description=""):
        task_id = str(uuid4())
        task = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "description": description,
            "progress": 0,
            "processed": 0,
            "total": 0,
            "success": 0,
            "created_at": time.time(),
            "updated_at": time.time(),
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
                self.__tasks[task_id]["updated_at"] = time.time()
                return True
        return False

    def delete_task(self, task_id):
        with self.__lock:
            if task_id in self.__tasks:
                del self.__tasks[task_id]
                return True
        return False
