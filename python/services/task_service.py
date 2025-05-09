class TaskService:
    def __init__(self):
        self.tasks = []  # 模拟数据库

    def get_all_tasks(self):
        return self.tasks

    def create_task(self, task_data):
        # 这里可以添加业务逻辑，如数据验证、持久化等
        self.tasks.append(task_data)
        return task_data
