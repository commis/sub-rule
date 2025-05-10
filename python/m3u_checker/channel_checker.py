import os

import av
import m3u8
import requests

from m3u_checker import channel_service
from m3u_checker.channel import ChannelInfo


class ChannelExtractor:
    def __init__(self, url, start=0, size=1):
        self.__template_url = url
        self.__start = start
        self.__size = size

    def __check_m3u8_url(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except requests.RequestException:
            return None

    def __extract_ts_urls(self, m3u8_content):
        m3u8_obj = m3u8.loads(m3u8_content)
        return m3u8_obj.segments.uri

    def __download_ts(self, ts_url, ts_filename):
        try:
            response = requests.get(ts_url)
            if response.status_code == 200:
                with open(ts_filename, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except requests.RequestException:
            return False

    def __extract_channel_stream(self, ts_filename):
        try:
            container = av.open(ts_filename)
            for stream in container.streams:
                print(f"Stream type: {stream.type}, Codec: {stream.codec_context.codec.name}")
            return "Extracted some basic stream info"
        except Exception as e:
            print(f"Error extracting channel info: {e}")
            return None
        finally:
            if os.path.exists(ts_filename):
                os.remove(ts_filename)

    def __extract_channel_name(self, m3u8_content):
        lines = m3u8_content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('#EXTINF'):
                parts = line.split(',')
                if len(parts) > 1:
                    return parts[1]
        return None

    def check_single(self, url, id) -> ChannelInfo | None:
        channel_info = ChannelInfo(id, url)
        m3u8_content = self.__check_m3u8_url(url)
        if m3u8_content:
            channel_info.set_channel_name(self.__extract_channel_name(m3u8_content))
            ts_urls = self.__extract_ts_urls(m3u8_content)
            if len(ts_urls) == 0:
                channel_info = None
            # for i, ts_url in enumerate(ts_urls):
            #     if not ts_url.startswith('http'):
            #         base = result.url.rsplit('/', 1)[0]
            #         ts_url = f"{base}/{ts_url}"
            #     ts_filename = f"temp_{index}_{i}.ts"
            #     if self.download_ts(ts_url, ts_filename):
            #         channel_info = self.extract_channel_stream(ts_filename)
            #         if channel_info:
            #             print(f"有效地址: {result.url}, TS片段: {ts_url}, 频道信息: {channel_info}")
            #         else:
            #             print(f"有效地址: {result.url}, TS片段: {ts_url}, 未找到频道信息")
            #     else:
            #         print(f"无效TS地址: {ts_url}")
        else:
            print(f"无效m3u8地址: {url}")

        return channel_info

    def check_batch(self, task_status=None):
        success_count = 0
        total_count = self.__size
        for i, index in enumerate(range(self.__start, self.__start + self.__size)):
            url = self.__template_url.format(i=index)
            channel_info = self.check_single(url, index)
            if channel_info:
                channel_service.add_channel(channel_info)
                success_count += 1

            if task_status:
                task_status["progress"] = (i + 1) / total_count * 100
                task_status["processed"] = i + 1
                task_status["success"] = success_count

        return success_count
