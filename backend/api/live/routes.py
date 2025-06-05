from typing import Optional

from fastapi import APIRouter, Body, Query, status
from fastapi.responses import Response
from starlette.background import BackgroundTasks

from api.live.converter import LiveConverter
from api.live.merger import LiveMerger
from core.logger_factory import LoggerFactory
from models.task_response import TaskResponse
from services import channel_manager, task_manager
from services.checker import ChannelChecker
from utils.handler import handle_exception
from utils.parser import Parser

router = APIRouter(prefix="/live", tags=["Live处理器"])
logger = LoggerFactory.get_logger(__name__)


@router.post("/cvt/txt", summary="TXT格式转换为M3U格式", response_model=str)
def convert_txt_to_m3u(
        txt_data: str = Body(..., media_type="text/plain", min_length=1, description="待转换的TXT格式直播源数据")):
    """
    将TXT格式的直播源数据转换为M3U格式
    """
    try:
        converter = LiveConverter()
        result = converter.txt_to_m3u(txt_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        handle_exception(f"conversion failed: {str(e)}")


@router.post("/cvt/m3u", summary="M3U格式转换为TXT格式", response_model=str)
def convert_m3u_to_txt(
        m3u_data: str = Body(..., media_type="text/plain", min_length=1, description="待转换的M3U格式直播源数据")):
    """
    将M3U格式的直播源数据转换为TXT格式
    """
    try:
        if not m3u_data.strip():
            handle_exception("invalidate input: empty text", status.HTTP_400_BAD_REQUEST)

        converter = LiveConverter()
        result = converter.m3u_to_txt(m3u_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        handle_exception(f"conversion failed: {str(e)}")


@router.post("/mgr/txt", summary="合并TXT格式直播源并选择最优", response_model=str)
def merge_live_sources(
        txt_data: str = Body(..., media_type="text/plain", min_length=1, description="待合并的TXT格式直播源数据"),
        top_n: int = Query(3, ge=1, le=10, description="选择排名前N的直播源(1-10)")):
    """
    合并TXT格式的直播源数据并选择最优的前N个
    """
    try:
        if not txt_data.strip():
            handle_exception("invalidate input: empty text", status.HTTP_400_BAD_REQUEST)

        live_data = Parser.get_channel_data(txt_data)
        merger = LiveMerger(live_data)
        merger.find_top_hosts(n=top_n)
        result = merger.format_output()
        return Response(content=result, media_type="text/plain")
    except ValueError as ve:
        handle_exception(f"parse channel data failed: {str(ve)}")
    except Exception as e:
        handle_exception(f"merge live sources failed: {str(e)}")


@router.post("/chr/txt", summary="检测TXT格式直播源有效性", response_model=TaskResponse)
def check_live_sources(
        background_tasks: BackgroundTasks,
        txt_data: str = Body(..., media_type="text/plain", min_length=1, description="待合并的TXT格式直播源数据"),
        is_clear: Optional[bool] = Query(True, description="是否清空已有频道数据"),
        thread_size: Optional[int] = Query(20, ge=2, le=64, description="并发线程数上限50")):
    """
    检测TXT格式直播源有效性
    """
    try:
        if not txt_data:
            handle_exception("invalidate input: empty text", status.HTTP_400_BAD_REQUEST)

        if is_clear:
            channel_manager.clear()

        Parser.load_channel_data(txt_data)
        total_count = channel_manager.total_count()
        if total_count <= 0:
            channel_manager.clear()
            handle_exception(f"invalidate input: no valid channel data found")

        task_id = task_manager.create_task(
            url="",
            total=total_count,
            type="update_live_sources",
            description=f"检查TXT直播源有效性"
        )

        def run_check_live_task() -> None:
            """后台运行的批量检查任务"""
            try:
                task_manager.update_task(task_id, status="running")
                task = task_manager.get_task(task_id)

                checker = ChannelChecker()
                success_count = checker.update_batch_live(threads=thread_size, task_status=task)
                task.update({
                    "status": "completed",
                    "result": {"success": success_count}
                })
            except Exception as re:
                logger.error(f"check live sources task failed: {str(re)}", exc_info=True)
                task_manager.update_task(task_id, status="error", error=str(re))

        background_tasks.add_task(run_check_live_task)
        return TaskResponse(data={"task_id": task_id})
    except Exception as e:
        handle_exception(f"check live sources failed: {str(e)}")
