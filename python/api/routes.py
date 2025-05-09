from flask import request, jsonify

from api import api_bp
from services import task_service


@api_bp.route('/colors/<palette>/', methods=['GET'])
def colors(palette):
    """Example endpoint returning a list of colors by palette
    This is using docstrings for specifications.
    ---
    parameters:
      - name: palette
        in: path
        type: string
        enum: ['all', 'rgb', 'cmyk']
        required: true
        default: all
    definitions:
      Palette:
        type: object
        properties:
          palette_name:
            type: array
            items:
              $ref: '#/definitions/Color'
      Color:
        type: string
    responses:
      200:
        description: A list of colors (may be filtered by palette)
        schema:
          $ref: '#/definitions/Palette'
        examples:
          rgb: ['red', 'green', 'blue']
    """
    all_colors = {
        'cmyk': ['cyan', 'magenta', 'yellow', 'black'],
        'rgb': ['red', 'green', 'blue']
    }
    if palette == 'all':
        result = all_colors
    else:
        result = {palette: all_colors.get(palette)}

    return jsonify(result)


@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取任务列表
    ---
    responses:
      200:
        description: 任务列表
        schema:
          type: array
          items:
            $ref: '#/definitions/Task'
    """
    return jsonify(task_service.get_all_tasks())


@api_bp.route('/tasks', methods=['POST'])
def create_task():
    """
    创建新任务
    ---
    parameters:
      - in: body
        name: task
        required: true
        schema:
          $ref: '#/definitions/Task'
    responses:
      201:
        description: 任务创建成功
        schema:
          $ref: '#/definitions/Task'
    """
    task = request.json
    return jsonify(task_service.create_task(task)), 201
