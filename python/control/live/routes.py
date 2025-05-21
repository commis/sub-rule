from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import Response

from control.live.converter import LiveConverter
from control.live.merger import LiveMerger
from utils.parser import parse_channel_data

router = APIRouter(prefix="/live", tags=["Live处理器"])


@router.post('/cvt/txt', summary="转换频道数据（TXT格式）")
def live_convert_txt(txt_data: str = Body(..., media_type="text/plain")):
    try:
        if not txt_data.strip():
            raise HTTPException(status_code=400, detail="无效输入：空文本")

        converter = LiveConverter()
        result = converter.txt_to_m3u(txt_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/cvt/m3u', summary="转换频道数据（M3U格式）")
def live_convert_m3u(m3u_data: str = Body(..., media_type="text/plain")):
    try:
        if not m3u_data.strip():
            raise HTTPException(status_code=400, detail="无效输入：空文本")

        converter = LiveConverter()
        result = converter.m3u_to_txt(m3u_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/mgr/txt', summary="合并直播源（TXT格式）")
def live_merge_txt(txt_data: str = Body(..., media_type="text/plain")):
    try:
        if not txt_data.strip():
            raise HTTPException(status_code=400, detail="无效输入：空文本")

        live_data = parse_channel_data(txt_data)

        merger = LiveMerger(live_data)
        merger.find_top_hosts()
        result = merger.format_output()

        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
