import threading

from core.singleton import singleton
from datastruct.auto_sort_utils import mixed_sort_key
from datastruct.channel_info import ChannelInfo


@singleton
class ChannelManager:
    def __init__(self):
        self._channels = []
        self._lock = threading.RLock()

    def count(self):
        with self._lock:
            return len(self._channels)

    def clear(self):
        with self._lock:
            self._channels = []

    def get_channels(self, max_speed: int = 10000):
        with self._lock:
            filtered_channels = [channel for channel in self._channels if channel.speed <= max_speed]
            return sorted(filtered_channels, key=lambda ch: mixed_sort_key(ch.name))

    def add_channel(self, channel_info: ChannelInfo):
        with self._lock:
            if channel_info:
                self._channels.append(channel_info)

    def channel_ids(self):
        with self._lock:
            ids = [channel.id for channel in self._channels]
            return ids


channel_manager = ChannelManager()
