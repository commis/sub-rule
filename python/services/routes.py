from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, model_validator

from services import task_service

router = APIRouter(prefix="/task", tags=["任务管理器"])


class TaskQuery(BaseModel):
    id: str

    @model_validator(mode='after')
    def check_id(cls, values):
        if not values.id or values.id.strip() == '':
            raise ValueError("任务ID不能为空")
        return values


@router.get('/list', summary="获取任务列表")
def get_tasks():
    tasks = task_service.get_tasks()
    return tasks


@router.get('/{id}', summary="获取任务详情")
def get_task(task_id: TaskQuery = Depends(lambda id: TaskQuery(id=id))):
    task = task_service.get_task(task_id.id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务ID {task_id} 不存在")

    return task


@router.post('/delete', summary="删除任务")
def delete_task(task_id: TaskQuery = Depends(lambda id: TaskQuery(id=id))):
    task_service.delete_task(task_id.id)
    return {"message": f"任务ID {task_id} 已删除"}
