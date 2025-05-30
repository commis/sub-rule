import threading

from datastruct.auto_sort_utils import mixed_sort_key


class ChannelMap:
    def __init__(self):
        self._channels = {}
        self._lock = threading.RLock()

    def add_channel(self, channel_name, url):
        with self._lock:
            urls = self._channels.get(channel_name, [])
            urls.append(url)
            self._channels[channel_name] = urls

    def get_channels(self):
        with self._lock:
            return self._channels.keys()

    def to_string(self):
        with self._lock:
            lines = []
            for channel_name in sorted(self._channels.keys(), key=mixed_sort_key):
                urls = self._channels[channel_name]
                for url in urls:
                    lines.append(f"{channel_name},{url}")
            return "\n".join(lines)

    def write_to_file(self, file_handle):
        with self._lock:
            for channel_name in sorted(self._channels.keys(), key=mixed_sort_key):
                urls = self._channels[channel_name]
                for url in urls:
                    file_handle.write(f"{channel_name},{url}\n")
