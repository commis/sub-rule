import threading
from typing import Dict, Optional

from core.singleton import singleton


@singleton
class CategoryManager:
    """
    管理分类与图标映射关系的单例类
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._categories: Dict[str, Dict[str, object]] = {
            "央视频道": {"icon": "📺"},
            "央视精品": {
                "icon": "✨",
                "channels": [
                    "CCTV兵器科技", "CCTV风云剧场", "CCTV风云音乐", "CCTV风云足球", "CCTV高尔夫网球",
                    "CCTV怀旧剧场", "CCTV世界地理", "CCTV文化精品", "CCTV央视台球"
                ]
            },
            "卫视频道": {"icon": "📡"},
            "体育频道": {"icon": "⚽"},
            "纪录频道": {"icon": "📽"},
            "综艺频道": {"icon": "🎤"},
            "戏曲频道": {"icon": "🎭"},
            "电视剧场": {"icon": "📽️"},
            "电影频道": {"icon": "🎬"},
            "儿童频道": {"icon": "🧸"},
            "直播中国": {"icon": "📹"},
            "春晚频道": {"icon": "🏮"},
            "未分类组": {"icon": "📂"}
        }
        self._ignore_categories = ["直播中国"]

    def clear(self) -> None:
        """清空所有分类图标映射"""
        with self._lock:
            self._categories.clear()

    def is_ignore(self, category: str):
        """判断是否为忽略的分类"""
        return category in self._ignore_categories

    def get_groups(self):
        """获取所有分类的组"""
        with self._lock:
            return self._categories.keys()

    def exists(self, category: str) -> bool:
        """
        判断指定分类是否存在
        """
        with self._lock:
            return category in self._categories

    def get_category_info(self, category_name: str) -> Optional[Dict[str, object]]:
        """
        获取指定分类的图标
        """
        with self._lock:
            return self._categories.get(category_name)

    def get_category_name(self, channel_name: str) -> Optional[(str)]:
        """
        根据频道名称获取分类信息
        """
        with self._lock:
            if not channel_name:
                return None

            for category_name, category_info in self._categories.items():
                if "channels" in category_info:
                    channel_list = category_info["channels"]
                    if channel_name in channel_list:
                        return category_name

            return None

    def update_category(self, category_infos: Dict[str, Dict[str, object]]) -> None:
        """
        更新分类图标映射
        """
        with self._lock:
            self._categories.update(category_infos)

    def remove_category(self, category_name: str) -> None:
        """
        移除指定分类的图标映射
        """
        with self._lock:
            self._categories.pop(category_name, None)

    def list_categories(self) -> Dict[str, object]:
        """获取所有分类图标映射的副本"""
        with self._lock:
            return self._categories.copy()


category_manager = CategoryManager()
