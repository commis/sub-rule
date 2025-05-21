import os
import re
import time

import av
import m3u8
import requests

from datastruct import ChannelInfo
from service import channel_manager


class ChannelExtractor:
    def __init__(self, url, start=0, size=1):
        self.__template_url = url
        self.__start = start
        self.__size = size

    def check_single(self, url, cid):
        # 第一阶段：基础验证
        m3u8_content = self.__check_m3u8_url(url)
        if not m3u8_content:
            return None

        # 第二阶段：结构验证
        # is_valid, reason = self.__check_m3u8_validity(m3u8_content)
        # if not is_valid:
        #     return None

        # 第三阶段：TS验证
        base_url = url.rsplit('/', 1)[0]
        ts_urls = self.__extract_ts_urls(m3u8_content)
        ts_valid, ts_reason, tested_urls = self.__check_ts_availability(ts_urls, base_url)
        if not ts_valid:
            return None

        # 第四阶段：测速
        # speed = self.__benchmark_speed(tested_urls)

        # 第五阶段：元数据提取
        channel = ChannelInfo(cid, url)
        channel.set_speed(0)
        channel.set_channel_name(self.__extract_channel_name(m3u8_content, cid, url))
        channel.set_resolution(self.__detect_resolution(tested_urls[0]))

        return channel

    def __check_m3u8_url(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except requests.RequestException:
            return None

    def __check_m3u8_validity(self, m3u8_content):
        """增强版M3U8有效性验证"""
        # 基础验证
        if not m3u8_content.startswith("#EXTM3U"):
            return False, "缺少EXTM3U头"

        # 结构验证
        required_tags = ["#EXT-X-VERSION", "#EXT-X-MEDIA-SEQUENCE"]
        missing_tags = [tag for tag in required_tags if tag not in m3u8_content]
        if missing_tags:
            return False, f"缺少必要标签: {', '.join(missing_tags)}"

        return True, "结构完整"

    def __check_ts_availability(self, ts_urls, base_url):
        """深度TS片段可用性检查"""
        success = 0
        tested_urls = []

        # 测试前3个TS片段
        for ts in ts_urls[:3]:
            full_url = ts if ts.startswith("http") else f"{base_url}/{ts}"
            if self.__validate_ts(full_url):
                success += 1
                tested_urls.append(full_url)

        if success == 0:
            return False, "所有TS片段不可用", []
        return True, f"{success}/3 片段可用", tested_urls

    def __validate_ts(self, ts_url):
        """深度TS验证（包含基础下载）"""
        try:
            with requests.get(ts_url, stream=True, timeout=8) as res:
                if res.status_code != 200:
                    return False

            # 验证TS头部（至少包含PAT/PMT）
            headers = {'Range': 'bytes=0-1023'}
            with requests.get(ts_url, headers=headers, timeout=5) as res:
                return b'\x47' in res.content  # 检查TS包头标识
        except:
            return False

    def __extract_ts_urls(self, m3u8_content):
        m3u8_obj = m3u8.loads(m3u8_content)
        return m3u8_obj.segments.uri

    def __benchmark_speed(self, ts_urls):
        """带宽基准测试"""
        total_size = 0  # 字节
        total_time = 0  # 秒

        # 测试前2个可用TS
        for url in ts_urls[:2]:
            try:
                start = time.time()

                # 下载前512KB用于测速
                with requests.get(url, stream=True, timeout=10) as res:
                    res.raise_for_status()
                    chunk_size = 1024  # 1KB
                    for _ in range(512):  # 512 * 1KB = 512KB
                        chunk = next(res.iter_content(chunk_size), b'')
                        if not chunk:
                            break

                duration = time.time() - start
                if duration > 0:
                    total_size += 512 * 1024  # 累计512KB
                    total_time += duration
            except:
                continue

        if total_time == 0:
            return 0

        # 计算平均速度（KB/s）
        return (total_size / 1024) / total_time

    def __extract_channel_name(self, m3u8_content, id, url):
        # 方案1: 从EXTINF行提取
        channel_name = self.__extract_from_extinf(m3u8_content)
        if channel_name:
            return channel_name

        # 方案2: 从Content-Disposition头提取
        channel_name = self.__extract_from_content_disposition(url)
        if channel_name:
            return channel_name

        # 所有方案失败时返回默认名称
        return f"频道-{id}"

    def __extract_from_extinf(self, m3u8_content):
        """
        强化版EXTINF解析逻辑（禁止使用TS文件名）
        匹配策略：
        1. 优先捕获 tvg-name 属性
        2. 捕获逗号后的显示名称
        3. 无有效名称时返回None
        """
        extinf_pattern = re.compile(
            r'^#EXTINF:\s*'
            r'(?P<duration>-?\d+\.?\d*)\s*'  # 捕获时长
            r'(?:tvg-name=(?P<qt1>[\'"]?)(?P<tvg_name>[^\'",#]+?)(?P=qt1)\s*)?'  # 修复括号
            r'(?:,?\s*(?P<display_name>[^#]+?))?'  # 显示名称
            r'\s*(?:#.*)?$',  # 注释部分
            re.IGNORECASE | re.MULTILINE
        )

        candidates = []
        for line in m3u8_content.splitlines():
            if not line.startswith('#EXTINF'):
                continue

            match = extinf_pattern.match(line)
            if not match:
                continue

            groups = match.groupdict()
            # 优先级1：tvg-name（带/不带引号）
            if groups['tvg_name']:
                clean_name = groups['tvg_name'].strip('\'"')
                if clean_name:
                    return clean_name

            # 优先级2：显示名称（需清洗）
            if groups['display_name']:
                display = groups['display_name'].strip()
                # 过滤无效名称（纯数字、空值等）
                if display and not display.replace('.', '').isdigit():
                    candidates.append(display)

        # 选择最优显示名称（最长非空值）
        if candidates:
            return max(candidates, key=lambda x: len(x))

        return None

    def __extract_from_content_disposition(self, url):
        """
        方案3: 从Content-Disposition头提取
        """
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if 'content-disposition' in response.headers:
                cd_header = response.headers['content-disposition']
                filename_match = re.findall("filename=(.+)", cd_header)
                if filename_match:
                    filename = filename_match[0].strip('";')
                    return os.path.splitext(filename)[0]
        except:
            pass
        return None

    def __detect_resolution(self, ts_url):
        """解析视频分辨率"""
        try:
            container = av.open(ts_url)
            video_stream = next(s for s in container.streams if s.type == 'video')
            return f"{video_stream.width}x{video_stream.height}"
        except:
            return "未知"

    def check_batch(self, task_status=None):
        success_count = 0
        total_count = self.__size
        for i, index in enumerate(range(self.__start, self.__start + self.__size)):
            url = self.__template_url.format(i=index)
            channel_info = self.check_single(url, index)
            if channel_info:
                channel_manager.add_channel(channel_info)
                success_count += 1

            if task_status:
                task_status["progress"] = (i + 1) / total_count * 100
                task_status["processed"] = i + 1
                task_status["success"] = success_count

        return success_count
