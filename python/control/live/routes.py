from typing import Optional

from fastapi import APIRouter, Body, Query, status, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field

from control.live.converter import LiveConverter
from control.live.merger import LiveMerger
from core.logger_factory import LoggerFactory
from datastruct.task_response import TaskResponse
from service.checker import ChannelExtractor
from service.group import group_manager
from service.task import task_manager
from utils.handler import handle_exception
from utils.parser import parse_channel_data, parse_sitemap_data

router = APIRouter(prefix="/live", tags=["Live处理器"])
logger = LoggerFactory.get_logger(__name__)


class UpdateLiveRequest(BaseModel):
    """更新直播源请求"""
    output: str = Field(default="/tmp/result-1.txt", description="直播源输出文件名")
    url: Optional[str] = Field(default="https://live.izbds.com/sitemap.xml", description="直播源同步URL")
    is_clear: Optional[bool] = Field(True, description="是否清空已有频道数据")
    thread_size: Optional[int] = Field(20, ge=2, le=64, description="并发线程数上限50")
    low_limit: Optional[int] = Field(100, ge=50, le=300, description="自动更新频道数量下限")


@router.post("/cvt/txt", summary="TXT格式转换为M3U格式", response_model=str, response_class=Response)
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


@router.post("/cvt/m3u", summary="M3U格式转换为TXT格式", response_model=str, response_class=Response)
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


@router.post("/mgr/txt", summary="合并TXT格式直播源并选择最优", response_model=str, response_class=Response)
def merge_live_sources(
        txt_data: str = Body(..., media_type="text/plain", min_length=1, description="待合并的TXT格式直播源数据"),
        top_n: int = Query(3, ge=1, le=10, description="选择排名前N的直播源(1-10)")):
    """
    合并TXT格式的直播源数据并选择最优的前N个
    """
    try:
        if not txt_data.strip():
            handle_exception("invalidate input: empty text", status.HTTP_400_BAD_REQUEST)

        live_data = parse_channel_data(txt_data)
        merger = LiveMerger(live_data)
        merger.find_top_hosts(n=top_n)
        result = merger.format_output()
        return Response(content=result, media_type="text/plain")
    except ValueError as ve:
        handle_exception(f"parse channel data failed: {str(ve)}")
    except Exception as e:
        handle_exception(f"merge live sources failed: {str(e)}")


@router.post("/update", summary="自动更新直播源", response_model=TaskResponse)
def update_live_sources(request: UpdateLiveRequest, background_tasks: BackgroundTasks) -> TaskResponse:
    """
    自动更新直播源数据
    """
    try:
        if request.is_clear:
            group_manager.clear()

        live_data = parse_sitemap_data(request.url)
        total_count = len(live_data)
        if total_count <= request.low_limit:
            handle_exception(f"live sources count is too low: {total_count} (less than {request.low_limit})")

        task_id = task_manager.create_task(
            url=request.url,
            total=total_count,
            type="update_live_sources",
            description=f"output: {request.output}"
        )

        def run_update_live_task() -> None:
            """后台运行的批量检查任务"""
            try:
                task_manager.update_task(task_id, status="running")
                task = task_manager.get_task(task_id)

                extractor = ChannelExtractor(request.url)
                success_count = extractor.update_batch_live(
                    threads=request.thread_size,
                    live_data=live_data,
                    output_file=request.output,
                    task_status=task
                )

                task_manager.update_task(
                    task_id,
                    status="completed",
                    result={
                        "success": success_count
                    }
                )
            except Exception as re:
                logger.error(f"update live sources task failed: {str(re)}", exc_info=True)
                task_manager.update_task(task_id, status="error", error=str(re))

        background_tasks.add_task(run_update_live_task)
        return TaskResponse(data={"task_id": task_id})
    except ValueError as ve:
        handle_exception(str(ve), status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"update live sources request failed: {str(e)}", exc_info=True)
        handle_exception("update live sources request failed")


@router.get("/update/txt", summary="获取更新频道列表(TXT格式)", response_class=Response)
def get_update_channels():
    """获取所有可用频道的TXT格式列表"""
    try:
        content = group_manager.to_string()
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        logger.error(f"obtain update channels failed: {str(e)}", exc_info=True)
        handle_exception("obtain update channels failed")
