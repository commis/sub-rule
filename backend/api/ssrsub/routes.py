from fastapi import APIRouter
from fastapi.responses import Response

from services.subscribe import subscribe_service
from utils.handler import handle_exception

router = APIRouter(prefix="/ssrsub", tags=["VPN白嫖订阅"])


@router.get("/clash", summary="获取clash订阅节点列表", response_model=str)
def get_tasks():
    """获取clash订阅节点列表"""
    try:
        content = subscribe_service.get_clash_subscribe("ssrsub_v2ray")
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        handle_exception(f"occur error when get clash subscribe: {str(e)}")
