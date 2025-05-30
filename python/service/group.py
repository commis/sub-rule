import threading

from core.singleton import singleton
from datastruct.channel_map import ChannelMap


@singleton
class GroupManager:
    def __init__(self):
        self._groups = {}
        self._lock = threading.RLock()

    def clear(self):
        with self._lock:
            self._groups.clear()

    def add_group(self, name, channel_name, channel_url):
        with self._lock:
            if name not in self._groups:
                self._groups[name] = ChannelMap()
            self._groups[name].add_channel(channel_name, channel_url)

    def get_groups(self):
        with self._lock:
            return list(self._groups.keys())

    def get_channels(self, name) -> ChannelMap:
        channel_map = None
        with self._lock:
            if name in self._groups:
                channel_map = self._groups[name]
        return channel_map

    def to_string(self) -> str:
        from service.category import category_manager
        with self._lock:
            result = []
            for group_name, channel_map in self._groups.items():
                icon = category_manager.get_category_icon(group_name)
                if icon:
                    result.append(f"{icon}{group_name},#genre#")
                    result.append(channel_map.to_string())
                    result.append("")
            return "\n".join(result).strip()

    def write_to_file(self, file_handle):
        from service.category import category_manager
        with self._lock:
            for group_name, channel_map in self._groups.items():
                icon = category_manager.get_category_icon(group_name)
                if icon:
                    file_handle.write(f"{icon}{group_name},#genre#\n")
                    channel_map.write_to_file(file_handle)
                    file_handle.write("\n")


group_manager = GroupManager()
