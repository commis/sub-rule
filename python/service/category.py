import threading
from typing import Dict

from core.singleton import singleton


@singleton
class CategoryManager:
    """
    管理分类与图标映射关系的单例类

    使用线程安全的方式维护分类名称与图标之间的映射关系
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._category_icons: Dict[str, str] = {
            "央视频道": "📺",
            "央视精品": "🏆",
            "卫视频道": "🌍",
            "体育频道": "⚽",
            "综艺频道": "🎤",
            "戏曲频道": "🪭",
            "电视剧场": "🎭",
            "电影频道": "🎬",
            "儿童频道": "🎥"
        }

    def clear(self) -> None:
        """清空所有分类图标映射"""
        with self._lock:
            self._category_icons.clear()  # 修正：使用字典的clear方法

    def is_not_exist(self, category: str) -> bool:
        """
        判断指定分类是否不存在
        """
        with self._lock:
            return category not in self._category_icons

    def get_category_icon(self, category_name: str) -> str:
        """
        获取指定分类的图标
        """
        with self._lock:
            return self._category_icons.get(category_name)

    def update_category_icons(self, category_icons: Dict[str, str]) -> None:
        """
        更新分类图标映射
        """
        with self._lock:
            if isinstance(category_icons, dict):
                self._category_icons.update(category_icons)
            else:
                raise TypeError("category_icons参数必须是字典类型")

    def remove_category(self, category_name: str) -> None:
        """
        移除指定分类的图标映射
        """
        with self._lock:
            self._category_icons.pop(category_name, None)

    def list_categories(self) -> Dict[str, str]:
        """获取所有分类图标映射的副本"""
        with self._lock:
            return self._category_icons.copy()


category_manager = CategoryManager()
