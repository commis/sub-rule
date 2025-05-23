from fastapi import APIRouter, Body, Query, status
from fastapi.responses import Response

from control.live.converter import LiveConverter
from control.live.merger import LiveMerger
from utils.handler import handle_exception
from utils.parser import parse_channel_data

router = APIRouter(prefix="/live", tags=["Live处理器"])


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
        handle_exception(f"转换失败: {str(e)}")


@router.post("/cvt/m3u", summary="M3U格式转换为TXT格式", response_model=str, response_class=Response)
def convert_m3u_to_txt(
        m3u_data: str = Body(..., media_type="text/plain", min_length=1, description="待转换的M3U格式直播源数据")):
    """
    将M3U格式的直播源数据转换为TXT格式
    """
    try:
        if not m3u_data.strip():
            handle_exception("无效输入：空文本", status.HTTP_400_BAD_REQUEST)

        converter = LiveConverter()
        result = converter.m3u_to_txt(m3u_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        handle_exception(f"转换失败: {str(e)}")


@router.post("/mgr/txt", summary="合并TXT格式直播源并选择最优", response_model=str, response_class=Response)
def merge_live_sources(
        txt_data: str = Body(..., media_type="text/plain", min_length=1, description="待合并的TXT格式直播源数据"),
        top_n: int = Query(3, ge=1, le=10, description="选择排名前N的直播源(1-10)")):
    """
    合并TXT格式的直播源数据并选择最优的前N个
    """
    try:
        if not txt_data.strip():
            handle_exception("无效输入：空文本", status.HTTP_400_BAD_REQUEST)

        live_data = parse_channel_data(txt_data)
        merger = LiveMerger(live_data)
        merger.find_top_hosts(n=top_n)
        result = merger.format_output()
        return Response(content=result, media_type="text/plain")
    except ValueError as ve:
        handle_exception(f"解析失败: {str(ve)}", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        handle_exception(f"合并失败: {str(e)}")
