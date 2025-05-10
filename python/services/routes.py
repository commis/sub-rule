from flask import jsonify, Blueprint

from services import task_service
from utils.api_utils import ApiUtils

bp = Blueprint('task', __name__, url_prefix='/task')
swagger_tags = [
    {
        "name": "任务管理器",
        "description": "任务管理的相关接口"
    }
]


@bp.route('/<task_id>', methods=['GET'])
def get_batch_status(task_id):
    """
    获取批量任务状态
    ---
    tags:
      - 任务管理器
    parameters:
      - in: path
        name: task_id
        type: string
        required: true
    responses:
      200:
        description: 任务状态
        schema:
          type: object
      404:
        description: 任务ID不存在
    """
    task = task_service.get_task(task_id)
    if not task:
        return ApiUtils.not_found_404(f"任务ID {task_id} 不存在")

    return jsonify(task)
