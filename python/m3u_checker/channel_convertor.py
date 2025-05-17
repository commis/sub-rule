import re
from typing import List

from m3u_checker.channel import ChannelInfo


class ChannelConvertor:
    """M3U与TXT格式频道数据相互转换工具"""

    def __init__(self):
        """初始化转换器"""
        self.extinf_pattern = re.compile(r'#EXTINF:(-?\d+),(.*)')

    def m3u_to_txt(self, m3u_data: str) -> str:
        resutl = ""
        channels = self.__parse_m3u_channels(m3u_data)
        for channel in channels:
            resutl += f"{channel.get_txt()}\n"
        return resutl

    def txt_to_m3u(self, txt_data: str) -> str:
        resutl = ""
        channels = self.__parse_txt_channels(txt_data)
        for channel in channels:
            resutl += f"{channel.get_m3u()}\n"
        return resutl

    def __parse_m3u_channels(self, m3u_data: str) -> List[ChannelInfo]:
        channels = []
        current_name = None

        lines = m3u_data.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                match = self.extinf_pattern.match(line)
                if match:
                    current_name = match.group(2)
            elif line.startswith('http') and current_name:
                parts = line.split('/')
                try:
                    id_part = next((part for part in reversed(parts) if part.isdigit()), None)
                    channel_id = int(id_part) if id_part else len(channels) + 1
                except:
                    channel_id = len(channels) + 1

                channel = ChannelInfo(channel_id, line)
                channel.channel_name = current_name
                channels.append(channel)
                current_name = None
        return channels

    def __parse_txt_channels(self, txt_data: str) -> List[ChannelInfo]:
        channels = []
        lines = txt_data.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 分割名称和URL
            parts = line.split(',', 1)
            if len(parts) != 2:
                continue

            name, url = parts
            try:
                # 尝试从URL路径中提取数字ID
                path_parts = url.split('/')
                id_part = next((part for part in reversed(path_parts) if part.isdigit()), None)
                channel_id = int(id_part) if id_part else len(channels) + 1
            except:
                channel_id = len(channels) + 1

            channel = ChannelInfo(channel_id, url)
            channel.channel_name = name
            channels.append(channel)
        return channels
