import threading
from typing import Dict, Optional

from core.singleton import singleton


@singleton
class CategoryManager:
    """
    管理分类与图标映射关系的单例类
    """
    _channel_relations: Dict[str, Dict[str, object]] = {}

    def __init__(self):
        # 分类信息，channels仅为配置，内存中的数据不存在
        self._categories: Dict[str, Dict[str, object]] = {
            "锻炼": {"icon": "🏃"},
            "央视": {
                "icon": "📺",
                "channels": [],
                "excludes": [
                    "CCTV风云音乐", "CCTV风云足球", "CCTV风云剧场", "CCTV怀旧剧场", "CCTV兵器科技", "CCTV世界地理",
                    "CCTV央视台球", "CCTV第一剧场", "军事评论", "农业致富",
                    "精选推荐", "熊猫直播", "直播中国", "支持作者", "老故事", "中学生"]
            },
            "卫视": {
                "icon": "📡",
                "channels": [],
                "excludes": []
            },
            "地方": {
                "icon": "📍",
                "channels": [],
                "excludes": []
            },
            "纪实": {
                "icon": "📜",
                "channels": ["探索发现", "地理中国", "人与自然", "中国村庄", "自然传奇", "航拍中国第二季"],
                "excludes": ["*"]
            },
            "体育": {
                "icon": "🏀",
                "channels": [],
                "excludes": []
            },
            "综艺": {
                "icon": "🎤",
                "channels": [],
                "excludes": []
            },
            "教育": {
                "icon": "📚",
                "channels": ["CETV1", "CETV2", "CETV4"],
                "excludes": []
            },
            "电影": {
                "icon": "🎬",
                "channels": [
                    "CHC电影", "CHC动作电影", "CHC家庭影院", "CHC影迷电影",
                    "经典香港电影", "抗战经典影片", "新片放映厅", "高清大片", "南方影视",
                    "东森电影", "凤凰电影", "黑莓电影", "龙华电影"
                ],
                "excludes": ['*']
            },
            "儿童": {
                "icon": "👶",
                "channels": ["哈哈炫动", "黑龙江少儿", "金鹰卡通", "卡酷少儿", "浙江少儿", "优漫卡通"],
                "excludes": []
            },
            "轮播": {
                "icon": "🔁",
                "channels": [
                    "让子弹飞", "拆弹专家1", "拆弹专家2", "寒战", "龙门飞甲",
                    "我不是药神", "人在囧途", "人在囧途之港囧", "人在囧途之泰囧",
                ],
                "excludes": []
            },
            "其他": {
                "icon": "📂",
                "channels": ["钱塘江"],
                "excludes": []
            },
            "直播": {"icon": "📹"},
            "熊猫": {"icon": "🐼"},
            "春晚": {"icon": "🏮"},
            "港台": {"icon": "🌉"},
            "海外": {"icon": "🌐"},
            "全球": {"icon": "🌏"},
        }
        self._lock = threading.RLock()
        self._ignore_categories = [
            "直播", "熊猫", "春晚", "港台", "海外", "全球"
        ]

        self._init_channel_relations()

    def _init_channel_relations(self):
        """初始化频道名称与分类的映射关系"""
        with self._lock:
            for category_name, category_info in self._categories.items():
                category_info.update({"name": category_name})
                category_info.update({"excludes": category_info.get("excludes", [])})
                channel_list = category_info.get("channels", [])
                for channel in channel_list:
                    self._channel_relations[channel] = category_info

    def is_ignore(self, category: str):
        """判断是否为忽略的分类"""
        return category in self._ignore_categories

    def is_exclude(self, category_info: {}, channel_name: str) -> bool:
        """判断是否为排除的频道"""
        channels = category_info.get("channels", [])
        excludes = category_info.get("excludes", [])
        return ('*' in excludes and channel_name not in channels) or channel_name in excludes

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

    def get_category_object(self, channel_name: str, category_name):
        """
        根据频道名称获取分类名称
        """
        if channel_name in self._channel_relations:
            return self._channel_relations[channel_name]
        else:
            info = self._categories.get(category_name)
            return self._categories.get("未分类组") if info is None else info

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
