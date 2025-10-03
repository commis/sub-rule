import threading
from typing import Dict

from core.singleton import singleton
from models.channel_info import ChannelList, ChannelInfo
from services import category_manager


class ChannelBaseModel:
    """
    频道基类，提供频道管理的基本功能
    """

    def __init__(self):
        self._channelGroups: Dict[str, ChannelList] = {}
        self._lock = threading.RLock()

    def clear(self):
        self._channelGroups.clear()

    def sort(self):
        fix_names = category_manager.get_groups()
        index_map = {name: i for i, name in enumerate(fix_names)}
        default_index = len(fix_names)  # 不在列表中的项排在末尾

        with self._lock:
            self._channelGroups = dict(
                sorted(
                    self._channelGroups.items(),
                    key=lambda item: index_map.get(item[0], default_index)
                )
            )

    def total_count(self):
        with self._lock:
            # 对于忽略处理的分类，不计算总数
            return sum(
                channel_list.count()
                for group_name, channel_list in self._channelGroups.items()
                if not category_manager.is_ignore(group_name)
            )

    def add_channel(self, name: str, channel_name, channel_url, id: int = 0):
        with self._lock:
            # 自动分类处理
            category_info = category_manager.get_category_object(channel_name, name)
            category_name = category_info.get('name')
            if category_name not in self._channelGroups:
                self._channelGroups[category_name] = ChannelList()
            channel_list = self._channelGroups[category_name]
            if not category_manager.is_exclude(category_info, channel_name):
                channel_list.add_channel(channel_name, channel_url, id)

    def add_channel_info(self, name, channel_info: ChannelInfo):
        if not name:
            name = channel_info.title
        with self._lock:
            if name not in self._channelGroups:
                self._channelGroups[name] = ChannelList()
            channel_list = self._channelGroups[name]
            channel_list.add_channel_info(channel_info)

    def get_groups(self):
        with self._lock:
            return self._channelGroups.keys()

    def get_channel_list(self, group_name) -> ChannelList:
        with self._lock:
            if group_name in self._channelGroups:
                return self._channelGroups[group_name]
        return ChannelList()

    def channel_ids(self):
        with self._lock:
            result = []
            for _, channel_list in self._channelGroups.items():
                result.append(channel_list.get_channle_ids())
            return sorted(result)

    def to_m3u_string(self) -> str:
        with self._lock:
            result = ["#EXTM3U"]
            for group_name, channel_list in self._channelGroups.items():
                result.append(channel_list.get_m3u(group_name))
            return "\n".join(result).strip()

    def to_txt_string(self) -> str:
        from services.category import category_manager
        with self._lock:
            result = []
            for group_name, channel_list in self._channelGroups.items():
                category_info = category_manager.get_category_info(group_name)
                icon = "" if not category_info else category_info.get("icon", "")
                result.append(f"{icon}{group_name},#genre#")
                result.append(channel_list.get_txt())
                result.append("")
            return "\n".join(result).strip()

    def write_to_txt_file(self, file_handle):
        from services.category import category_manager
        with self._lock:
            for group_name, channel_list in self._channelGroups.items():
                category_info = category_manager.get_category_info(group_name)
                icon = category_info.get("icon", "")
                file_handle.write(f"{icon}{group_name},#genre#\n")
                channel_list.write_to_txt_file(file_handle)
                file_handle.write("\n")

    def write_to_m3u_file(self, file_handle):
        with self._lock:
            file_handle.write("#EXTM3U\n")
            for group_name, channel_list in self._channelGroups.items():
                file_handle.write(channel_list.get_m3u(group_name))


@singleton
class ChannelManager(ChannelBaseModel):
    """
    频道管理器，管理所有频道信息
    """

    def __init__(self):
        super().__init__()


channel_manager = ChannelManager()
