import re
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

from m3u_checker import channel_service
from m3u_checker.channel_checker import ChannelExtractor
from m3u_checker.channel_convertor import ChannelConvertor
from services import task_service

router = APIRouter(prefix="/channel", tags=["M3U检测器"])


# 定义请求模型
class SingleCheckRequest(BaseModel):
    url: str = Field(..., description="频道URL")
    rule: str = Field(..., description="解析规则")

    @model_validator(mode='before')
    def validate_rule(cls, values):
        rule = values.get('rule')
        if not isinstance(rule, str) or not rule.strip():
            raise ValueError('解析规则不能为空')
        if '{i}' not in rule:
            raise ValueError('解析规则必须包含"{i}"')
        return values

    def extract_id(self, url: str) -> Optional[int]:
        # 构建正则表达式模式，要求{i}位置为数字，默认值为1
        pattern = re.escape(self.rule).replace('\\{i\\}', '(\\d+)')
        match = re.search(pattern, url)
        if match:
            return int(match.group(1))
        return 1


class BatchCheckRequest(BaseModel):
    url: str = Field(..., description="包含{i}占位符的URL")
    start: int = Field(1, description="起始频道ID", ge=1)
    size: int = Field(10, description="检查数量", ge=1)


class ChannelQuery(BaseModel):
    speed: int

    @model_validator(mode='after')
    def check_speed(cls, values):
        if not values.speed or values.speed.strip() == '':
            raise ValueError("任务ID不能为空")
        return values


@router.post('/single', summary="检查单个频道")
def check_single_channel(request: SingleCheckRequest):
    try:
        url = request.url
        id = request.extract_id(url)

        result = ""
        extractor = ChannelExtractor(url)
        channel_info = extractor.check_single(url, id)
        if channel_info:
            result = channel_info.get_all()
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/batch', summary="批量检查频道")
def check_batch_channels(request: BatchCheckRequest, background: BackgroundTasks):
    try:
        url = request.url
        start = request.start
        size = request.size

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

        background.add_task(run_batch_check)
        return {
            "code": 202,
            "message": "任务已接受",
            "data": {"task_id": task_id}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/batch/txt', summary="查询频道批量检查结果（TXT格式）")
def get_channels_txt():
    try:
        result = ""
        channels = channel_service.get_channels()
        for i, item in enumerate(channels, start=1):
            result += f"{item.get_txt()}\n"
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/batch/m3u', summary="查询频道批量检查结果（M3U格式）")
def get_channels_m3u():
    try:
        result = ""
        channels = channel_service.get_channels()
        for i, item in enumerate(channels, start=1):
            result += f"{item.get_m3u()}\n"
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/txt', summary="转换频道数据（TXT格式）")
def convert_txt_channels(txt_data: str = Body(..., media_type="text/plain")):
    try:
        if not txt_data.strip():
            raise HTTPException(status_code=400, detail="无效输入：空文本")

        converter = ChannelConvertor()
        result = converter.txt_to_m3u(txt_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/m3u', summary="转换频道数据（M3U格式）")
def convert_m3u_channels(m3u_data: str = Body(..., media_type="text/plain")):
    try:
        if not m3u_data.strip():
            raise HTTPException(status_code=400, detail="无效输入：空文本")

        converter = ChannelConvertor()
        result = converter.m3u_to_txt(m3u_data)
        return Response(content=result, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
