import threading

from core.singleton import singleton


@singleton
class ChannelManager:
    def __init__(self):
        self.__channels = []
        self.__lock = threading.RLock()

    def count(self):
        with self.__lock:
            return len(self.__channels)

    def clear(self):
        with self.__lock:
            self.__channels = []

    def get_channels(self, max_speed: int = 10000):
        with self.__lock:
            return [channel for channel in self.__channels if channel.speed <= max_speed]

    def add_channel(self, channel_info):
        with self.__lock:
            if channel_info:
                self.__channels.append(channel_info)

    def channel_ids(self):
        with self.__lock:
            ids = [channel.id for channel in self.__channels]
            return ids
