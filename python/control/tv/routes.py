import re
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator, field_validator

from core.logger_factory import LoggerFactory
from datastruct.task_response import TaskResponse
from service.channel import channel_manager
from service.checker import ChannelExtractor
from service.task import task_manager
from utils.handler import handle_exception

router = APIRouter(prefix="/tv", tags=["M3U检测器"])
logger = LoggerFactory.get_logger(__name__)


class SingleCheckRequest(BaseModel):
    """单个频道检查请求模型"""
    url: str = Field(..., description="频道URL")
    rule: str = Field(default="/{i}/", description="解析规则，必须包含{i}占位符")

    @field_validator('url')
    def valid_url(cls, value):
        """验证URL格式是否有效"""
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                raise ValueError("无效的URL格式")
            return value
        except ValueError as e:
            raise ValueError(f"URL验证失败: {str(e)}")

    @field_validator('rule')
    def rule_contains_placeholder(cls, value):
        """验证规则中是否包含{i}占位符"""
        if '{i}' not in value:
            raise ValueError("规则必须包含{i}占位符")
        return value

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
    is_clear: Optional[bool] = Field(True, description="是否清空已有频道数据")
    thread_size: Optional[int] = Field(20, ge=2, le=64, description="并发线程数上限50")


class ChannelQuery(BaseModel):
    speed: int

    @model_validator(mode='after')
    def check_speed(cls, values):
        if not values.speed or values.speed.strip() == '':
            raise ValueError("任务ID不能为空")
        return values


@router.post("/single", summary="检查单个频道", response_class=Response)
def check_single_channel(request: SingleCheckRequest) -> Response:
    """检查单个电视频道并返回解析结果"""
    try:
        channel_id = request.extract_id(request.url)
        extractor = ChannelExtractor(request.url)
        channel_info = extractor.check_single(request.url, cid=channel_id, channel_name=None)

        if not channel_info:
            return Response(content="", media_type="text/plain")

        return Response(content=channel_info.get_all(), media_type="text/plain")

    except ValueError as ve:
        handle_exception(str(ve))
    except Exception as e:
        logger.error(f"single check failed: {str(e)}", exc_info=True)
        handle_exception("single check failed")


@router.post("/batch", summary="批量检查频道", response_model=TaskResponse)
def check_batch_channels(request: BatchCheckRequest, background_tasks: BackgroundTasks) -> TaskResponse:
    """异步批量检查多个电视频道"""
    try:
        if request.is_clear:
            channel_manager.clear()

        task_id = task_manager.create_task(
            url=request.url,
            total=request.size,
            type="batch_channel_check",
            description=f"从ID {request.start} 开始检查 {request.size} 个频道"
        )

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
            except Exception as re:
                logger.error(f"batch check failed: {str(re)}", exc_info=True)
                task_manager.update_task(task_id, status="error", error=str(e))

        background_tasks.add_task(run_batch_check_task)
        return TaskResponse(data={"task_id": task_id})
    except ValueError as ve:
        handle_exception(str(ve))
    except Exception as e:
        logger.error(f"batch check failed: {str(e)}", exc_info=True)
        handle_exception("batch check failed")


@router.get("/batch/txt", summary="获取频道列表(TXT格式)", response_class=Response)
def get_channels_txt():
    """获取所有可用频道的TXT格式列表"""
    try:
        channels = channel_manager.get_channels()
        content = "\n".join(channel.get_txt() for channel in channels)
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        logger.error(f"obtain channel txt list failed: {str(e)}", exc_info=True)
        handle_exception("obtain channel txt list failed")


@router.get("/batch/m3u", summary="获取频道列表(M3U格式)", response_class=Response)
def get_channels_m3u():
    """获取所有可用频道的M3U格式列表"""
    try:
        channels = channel_manager.get_channels()
        content = "#EXTM3U\n" + "\n".join(channel.get_m3u() for channel in channels)
        return Response(content=content, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        logger.error(f"obtain channel m3u list failed: {str(e)}", exc_info=True)
        handle_exception("obtain channel m3u list failed")
