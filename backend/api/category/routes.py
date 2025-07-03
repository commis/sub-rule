from typing import Dict

from fastapi import APIRouter, HTTPException, Body
from starlette import status

from services.category import category_manager
from utils.handler import handle_exception

router = APIRouter(prefix="/category", tags=["分类图标管理"])


@router.get("/icons", summary="获取所有分类图标", response_model=Dict[str, object])
def get_all_category_icons():
    """获取所有分类及其对应的图标"""
    return category_manager.list_categories()


@router.get("/icons/{category_name}", summary="获取单个分类图标", response_model=Dict[str, object])
def get_category_info(category_name: str):
    """获取指定分类的图标"""
    category_info = category_manager.get_category_info(category_name)
    if category_info is None:
        handle_exception(f"category '{category_name}' not found", status.HTTP_404_NOT_FOUND)
    return category_info


@router.post("/icons", summary="添加/更新分类图标", response_model=Dict[str, object])
def update_category_data(category_infos: Dict[str, object] = Body(..., description="分类图标映射字典")):
    """
    批量添加或更新分类图标
    """
    if not category_infos:
        handle_exception("icon data is empty", status.HTTP_400_BAD_REQUEST)

    try:
        category_manager.update_category(category_infos)
        return category_manager.list_categories()
    except Exception as e:
        handle_exception(str(e))


@router.delete("/icons/{category_name}", summary="删除分类图标", response_model=Dict[str, object])
def delete_category_icon(category_name: str):
    """
    删除指定分类的图标
    """
    if not category_manager.exists(category_name):
        raise HTTPException(status_code=404, detail=f"分类 '{category_name}' 不存在")

    category_manager.remove_category(category_name)
    return category_manager.list_categories()


@router.delete("/icons", summary="清空所有分类图标", response_model=Dict[str, object])
def clear_all_category_icons():
    """清空所有分类图标映射"""
    category_manager.clear()
    return category_manager.list_categories()
