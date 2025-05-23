import re
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

from control.tv.checker import ChannelExtractor
from core.logger_factory import LoggerFactory
from service import task_manager, channel_manager
from utils.handler import handle_exception

router = APIRouter(prefix="/tv", tags=["M3U检测器"])
logger = LoggerFactory.get_logger(__name__)


class SingleCheckRequest(BaseModel):
    """单个频道检查请求模型"""
    url: str = Field(..., description="频道URL")
    rule: str = Field(..., description="解析规则，必须包含{i}占位符")

    @model_validator(mode='before')
    def validate_rule(cls, value: str) -> str:
        """验证解析规则是否有效"""
        if not value or value.strip() == '':
            raise ValueError("解析规则不能为空")
        if "{i}" not in value:
            raise ValueError("解析规则必须包含{i}占位符")
        return value.strip()

    def extract_id(self, url: str) -> int:
        """从URL中提取频道ID，若未找到则返回1"""
        pattern = re.escape(self.rule).replace('\\{i\\}', '(\\d+)')
        match = re.search(pattern, url)
        return int(match.group(1)) if match else 1


class BatchCheckRequest(BaseModel):
    """批量频道检查请求模型"""
    url: str = Field(..., description="包含{i}占位符的基础URL")
    start: int = Field(1, ge=1, description="起始频道ID")
    size: int = Field(10, ge=1, le=1000, description="检查数量上限1000")
    is_clear: bool = Field(True, description="是否清空已有频道数据")
    thread_size: Optional[int] = Field(10, ge=1, le=50, description="并发线程数上限50")


class ChannelQuery(BaseModel):
    speed: int

    @model_validator(mode='after')
    def check_speed(cls, values):
        if not values.speed or values.speed.strip() == '':
            raise ValueError("任务ID不能为空")
        return values


class TaskResponse(BaseModel):
    """任务响应模型"""
    code: int = 202
    message: str = "任务已接受"
    data: Dict[str, str]


@router.post("/single", summary="检查单个频道", response_class=Response)
def check_single_channel(request: SingleCheckRequest) -> Response:
    """检查单个电视频道并返回解析结果"""
    try:
        channel_id = request.extract_id(request.url)
        extractor = ChannelExtractor(request.url)
        channel_info = extractor.check_single(request.url, channel_id)

        if not channel_info:
            return Response(content="", media_type="text/plain")

        return Response(content=channel_info.get_all(), media_type="text/plain")

    except ValueError as ve:
        handle_exception(str(ve), status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"单频道检查失败: {str(e)}", exc_info=True)
        handle_exception("单频道检查失败")


@router.post("/batch", summary="批量检查频道", response_model=TaskResponse)
def check_batch_channels(request: BatchCheckRequest, background_tasks: BackgroundTasks) -> TaskResponse:
    """异步批量检查多个电视频道"""
    try:
        if request.is_clear:
            channel_manager.clear()

        task_id = task_manager.create_task(
            url=request.url,
            type="batch_channel_check",
            description=f"从ID {request.start} 开始检查 {request.size} 个频道"
        )

        task_manager.update_task(task_id, total=request.size)

        def run_batch_check_task() -> None:
            """后台运行的批量检查任务"""
            try:
                task_manager.update_task(task_id, status="running")
                task = task_manager.get_task(task_id)

                extractor = ChannelExtractor(request.url, request.start, request.size)

                success_count = extractor.check_batch(
                    threads=request.thread_size,
                    task_status=task
                )

                success_ids = channel_manager.channel_ids()
                task_manager.update_task(
                    task_id,
                    status="completed",
                    result={
                        "success": success_count,
                        "channels": success_ids
                    }
                )
            except Exception as e:
                logger.error(f"批量检查任务失败: {str(e)}", exc_info=True)
                task_manager.update_task(task_id, status="error", error=str(e))

        background_tasks.add_task(run_batch_check_task)
        return TaskResponse(data={"task_id": task_id})
    except ValueError as ve:
        handle_exception(str(ve), status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"批量检查请求处理失败: {str(e)}", exc_info=True)
        handle_exception("批量检查任务创建失败")


@router.get("/batch/txt", summary="获取频道列表(TXT格式)", response_class=Response)
def get_channels_txt():
    """获取所有可用频道的TXT格式列表"""
    try:
        channels = channel_manager.get_channels()
        content = "\n".join(channel.get_txt() for channel in channels)
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        logger.error(f"获取TXT频道列表失败: {str(e)}", exc_info=True)
        handle_exception("获取频道列表失败")


@router.get("/batch/m3u", summary="获取频道列表(M3U格式)", response_class=Response)
def get_channels_m3u():
    """获取所有可用频道的M3U格式列表"""
    try:
        channels = channel_manager.get_channels()
        content = "#EXTM3U\n" + "\n".join(channel.get_m3u() for channel in channels)
        return Response(content=content, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        logger.error(f"获取M3U频道列表失败: {str(e)}", exc_info=True)
        handle_exception("获取频道列表失败")
