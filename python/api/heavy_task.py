import threading
import time

from api import api_bp
from flask import request, jsonify


@api_bp.route('/heavy_task', methods=['POST'])
def heavy_task():
    """
    模拟耗时任务
    ---
    parameters:
      - in: query
        name: seconds
        type: integer
        default: 5
        description: 任务执行时间（秒）
    responses:
      200:
        description: 任务启动成功
        schema:
          type: object
          properties:
            message:
              type: string
    """
    seconds = request.args.get('seconds', 5, type=int)

    def run_heavy_task():
        time.sleep(seconds)
        print(f"耗时任务执行完成（{seconds}秒）")

    threading.Thread(target=run_heavy_task).start()

    return jsonify({"message": f"耗时任务已启动，将在{seconds}秒后完成"}), 200
