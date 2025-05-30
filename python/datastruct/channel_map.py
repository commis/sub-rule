import threading

from datastruct.auto_sort_utils import mixed_sort_key


class ChannelMap:
    def __init__(self):
        self._channels = {}
        self._lock = threading.RLock()

    def add_channel(self, name, url):
        with self._lock:
            if name not in self._channels:
                self._channels[name] = []
            self._channels[name].append(url)

    def get_channels(self):
        with self._lock:
            return self._channels.keys()

    def get_urls(self, name):
        with self._lock:
            if name in self._channels:
                return self._channels[name]
        return []

    def remove_invalid_url(self, name, url):
        with self._lock:
            if name in self._channels:
                self._channels[name].remove(url)

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
