from .task_service import TaskService

# 单例模式
task_service = TaskService.get_instance()
