import threading

from flask import request, Blueprint

from services import task_service
from utils.api_utils import ApiUtils
from . import channel_service
from .channel_checker import ChannelExtractor
from .channel_convertor import ChannelConvertor

bp = Blueprint('channel', __name__, url_prefix='/channel')
swagger_tags = [
    {
        "name": "M3U检测器",
        "description": "检查M3U URL有效性的相关接口"
    }
]


@bp.route('/single', methods=['POST'])
def check_single_channel():
    """
    检查单个频道
    ---
    tags:
      - M3U检测器
    parameters:
      - in: body
        name: channel_single_data
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              description: 频道URL膜拜
            id:
              type: integer
              description: 频道ID
              default: 1
    responses:
      200:
        description: 检查结果
        schema:
          type: object
      400:
        description: 无效请求
        schema:
          type: object
    """
    try:
        data = request.get_json()
        if not data:
            return ApiUtils.invalid_request_400()

        id = data.get('id', 1)
        url = data.get('url')
        if not url:
            return ApiUtils.invalid_parameter_400("请求中必须包含url参数")

        extractor = ChannelExtractor(url)
        channel_info = extractor.check_single(url, id)
        return channel_info.get_all()
    except Exception as e:
        return ApiUtils.invalid_response_500(e)


@bp.route('/batch', methods=['POST'])
def check_batch_channels():
    """
    批量检查频道
    ---
    tags:
      - M3U检测器
    parameters:
      - in: body
        name: channel_batch_data
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              description: 频道URL
            start:
              type: integer
              description: 起始频道ID
            size:
              type: integer
              description: 频道数量
    responses:
      200:
        description: 检查结果
        schema:
          type: object
      400:
        description: 无效请求
        schema:
          type: object
    """
    try:
        data = request.json
        if not data:
            return ApiUtils.invalid_request_400()

        url = data.get('url')
        start = data.get('start', 1)
        size = data.get('size', 10)

        if not url or start <= 0:
            return ApiUtils.invalid_parameter_400("请求中必须包含url参数，或者开始频道ID无效")

        task_id = task_service.create_task(
            "batch_channel_check",
            f"Checking {size} channels starting from {start}"
        )
        task_service.update_task(task_id, total=size)

        def run_batch_check():
            try:
                channel_service.clear()
                task_service.update_task(task_id, status="running")

                task = task_service.get_task(task_id)
                extractor = ChannelExtractor(url, start, size)
                success_count = extractor.check_batch(task)

                # 更新任务完成状态
                success_ids = channel_service.channel_ids()
                task_service.update_task(
                    task_id,
                    status="completed",
                    result={
                        "success": success_count,
                        "channels": success_ids
                    })
            except Exception as e:
                task_service.update_task(task_id, status="error", error=str(e))

        # 启动后台线程
        threading.Thread(target=run_batch_check).start()
        return ApiUtils.sync_request_accepted_202(task_id)
    except Exception as e:
        return ApiUtils.invalid_response_500(e)


@bp.route('/batch/txt', methods=['GET'])
def get_channels_txt():
    """
    查询频道批量检查结果（TXT格式）
    ---
    tags:
      - M3U检测器
    responses:
      200:
        description: 检查结果
        schema:
          type: object
    """
    try:
        response = ""
        channels = channel_service.get_channels()
        for i, item in enumerate(channels, start=1):
            response += f"{item.get_txt()}\n"
        return response
    except Exception as e:
        return ApiUtils.invalid_response_500(e)


@bp.route('/batch/m3u', methods=['GET'])
def get_channels_m3u():
    """
    查询频道批量检查结果（M3U格式）
    ---
    tags:
      - M3U检测器
    responses:
      200:
        description: 检查结果
        schema:
          type: object
    """
    try:
        response = ""
        channels = channel_service.get_channels()
        for i, item in enumerate(channels, start=1):
            response += f"{item.get_m3u()}\n"
        return response
    except Exception as e:
        return ApiUtils.invalid_response_500(e)


@bp.route('/txt', methods=['POST'])
def convert_txt_channels():
    """
    转换频道数据（TXT格式）
    ---
    tags:
      - M3U转换器
    parameters:
      - in: body
        name: channel_convert_txt
        required: true
        schema:
          type: string
    responses:
      200:
        description: 检查结果
        schema:
          type: object
    """
    try:
        txt_data = request.data.decode('utf-8')
        if not txt_data:
            return ApiUtils.invalid_request_400()

        converter = ChannelConvertor()
        return converter.txt_to_m3u(txt_data)
    except Exception as e:
        return ApiUtils.invalid_response_500(e)


@bp.route('/m3u', methods=['POST'])
def convert_m3u_channels():
    """
    转换频道数据（M3U格式）
    ---
    tags:
      - M3U转换器
    parameters:
      - in: body
        name: channel_convert_m3u
        required: true
        schema:
          type: string
    responses:
      200:
        description: 检查结果
        schema:
          type: object
    """
    try:
        m3u_data = request.data.decode('utf-8')
        if not m3u_data:
            return ApiUtils.invalid_request_400()

        converter = ChannelConvertor()
        return converter.m3u_to_txt(m3u_data)
    except Exception as e:
        return ApiUtils.invalid_response_500(e)
