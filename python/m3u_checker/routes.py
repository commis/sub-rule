import threading

from flask import request, jsonify

from . import channel_bp, checker


@channel_bp.route('/single', methods=['POST'])
def check_single_channel():
    """
    检查单个频道
    ---
    parameters:
      - in: body
        name: channel
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              required: true
            timeout:
              type: integer
              default: 10
    responses:
      200:
        description: 检查结果
        schema:
          type: object
          properties:
            reachable:
              type: boolean
            latency:
              type: number
            status_code:
              type: integer
            message:
              type: string
    """
    data = request.json
    url = data.get('url')
    timeout = data.get('timeout', 10)

    result = checker.check_channel(url, timeout)
    return jsonify(result)


@channel_bp.route('/batch', methods=['POST'])
def check_batch_channels():
    """
    批量检查频道
    ---
    parameters:
      - in: body
        name: channels
        required: true
        schema:
          type: object
          properties:
            urls:
              type: array
              items:
                type: string
            timeout:
              type: integer
              default: 10
    responses:
      200:
        description: 任务已启动
        schema:
          type: object
          properties:
            task_id:
              type: string
            message:
              type: string
    """
    data = request.json
    urls = data.get('urls', [])
    timeout = data.get('timeout', 10)

    # 创建一个唯一的任务 ID
    import uuid
    task_id = str(uuid.uuid4())

    # 异步执行批量检查
    def run_batch_check():
        results = checker.check_channels(urls, timeout)
        # 这里可以将结果保存到数据库或文件
        print(f"批量检查完成，任务 ID: {task_id}")

    threading.Thread(target=run_batch_check).start()

    return jsonify({
        'task_id': task_id,
        'message': '批量检查任务已启动'
    })
