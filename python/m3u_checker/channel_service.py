import threading

from core.core_singleton import singleton


@singleton
class ChannelService:
    def __init__(self):
        self.channels = []
        self.__lock = threading.Lock()

    def count(self):
        with self.__lock:
            return len(self.channels)

    def clear(self):
        with self.__lock:
            self.channels = []

    def get_channels(self):
        with self.__lock:
            return self.channels

    def add_channel(self, channel_info):
        with self.__lock:
            if channel_info:
                self.channels.append(channel_info)

    def channel_ids(self):
        with self.__lock:
            ids = [channel.id for channel in self.channels]
            return ids
