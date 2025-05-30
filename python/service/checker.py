import concurrent
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import m3u8
import requests

from core.constants import Constants
from core.logger_factory import LoggerFactory
from datastruct.channel_info import ChannelInfo
from datastruct.counter import Counter
from service.group import group_manager

logger = LoggerFactory.get_logger(__name__)


class ChannelExtractor:
    def __init__(self, url, start=0, size=1):
        self._url = url
        self._start = start
        self._size = size

    def check_single(self, url, cid=0, channel_name=None):
        try:
            # 第一阶段：基础验证
            m3u8_content = self._check_m3u8_url(url)
            if not m3u8_content:
                return None

            # 第二阶段：结构验证
            # is_valid, reason = self.__check_m3u8_validity(m3u8_content)
            # if not is_valid:
            #     return None

            # 第三阶段：TS验证
            base_url = url.rsplit('/', 1)[0]
            ts_urls = self._extract_ts_urls(m3u8_content)
            ts_valid, ts_reason, tested_urls = self._check_ts_availability(ts_urls, base_url)
            if not ts_valid:
                return None

            # 第四阶段：测速
            # speed = self.__benchmark_speed(tested_urls)

            # 第五阶段：元数据提取
            tmp_channel_name = channel_name or self._extract_channel_name(m3u8_content, cid, url)
            channel = ChannelInfo(cid, url)
            channel.set_speed(0)
            channel.set_channel_name(tmp_channel_name)
            # channel.set_resolution(self.__detect_resolution(tested_urls[0]))
            return channel
        except Exception as e:
            logger.error(f"ChannelExtractor.check_single error: {e}")
            return None

    def _check_m3u8_url(self, url):
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.text
            return None
        except requests.RequestException:
            return None

    def _check_m3u8_validity(self, m3u8_content):
        """增强版M3U8有效性验证"""
        # 基础验证
        if not m3u8_content.startswith("#EXTM3U"):
            return False, "missing #EXTM3U header"

        # 结构验证
        required_tags = ["#EXT-X-VERSION", "#EXT-X-MEDIA-SEQUENCE"]
        missing_tags = [tag for tag in required_tags if tag not in m3u8_content]
        if missing_tags:
            return False, f"missing required tags: {', '.join(missing_tags)}"

        return True, "结构完整"

    def _check_ts_availability(self, ts_urls, base_url):
        """深度TS片段可用性检查"""
        success = 0
        tested_urls = []

        # 测试前3个TS片段
        for ts in ts_urls[:Constants.TS_SEGMENT_TEST_COUNT]:
            full_url = ts if ts.startswith("http") else f"{base_url}/{ts}"
            if self._validate_ts(full_url):
                success += 1
                tested_urls.append(full_url)

        if success == 0:
            return False, "all ts segments are not available", []
        return True, f"{success}/{Constants.TS_SEGMENT_TEST_COUNT} segments are available", tested_urls

    def _validate_ts(self, ts_url):
        """深度TS验证（包含基础下载）"""
        try:
            with requests.get(ts_url, stream=True, timeout=Constants.REQUEST_TIMEOUT) as res:
                if res.status_code != 200:
                    return False

            # 验证TS头部（至少包含PAT/PMT）
            headers = {'Range': 'bytes=0-1023'}
            with requests.get(ts_url, headers=headers, timeout=Constants.REQUEST_TIMEOUT) as res:
                return b'\x47' in res.content  # 检查TS包头标识
        except requests.RequestException:
            return False

    def _extract_ts_urls(self, m3u8_content):
        m3u8_obj = m3u8.loads(m3u8_content)
        return m3u8_obj.segments.uri

    def _benchmark_speed(self, ts_urls):
        """带宽基准测试"""
        total_size = 0  # 字节
        total_time = 0  # 秒

        # 测试前2个可用TS
        for url in ts_urls[:2]:
            try:
                start = time.time()

                # 下载前512KB用于测速
                with requests.get(url, stream=True, timeout=Constants.REQUEST_TIMEOUT) as res:
                    res.raise_for_status()
                    chunk_size = Constants.SPEED_TEST_CHUNK_SIZE  # 1KB
                    for _ in range(Constants.SPEED_TEST_BYTES):
                        chunk = next(res.iter_content(chunk_size), b'')
                        if not chunk:
                            break

                duration = time.time() - start
                if duration > 0:
                    total_size += (Constants.SPEED_TEST_BYTES * Constants.SPEED_TEST_CHUNK_SIZE)
                    total_time += duration
            except Exception as e:
                logger.error(f"ChannelExtractor.benchmark_speed error: {e}")
                continue

        if total_time == 0:
            return 0

        # 计算平均速度（KB/s）
        return (total_size / Constants.SPEED_TEST_CHUNK_SIZE) / total_time

    def _extract_channel_name(self, m3u8_content, id, url):
        # 方案1: 从EXTINF行提取
        channel_name = self._extract_from_extinf(m3u8_content)
        if channel_name:
            return channel_name

        # 方案2: 从Content-Disposition头提取
        channel_name = self._extract_from_content_disposition(url)
        if channel_name:
            return channel_name

        # 所有方案失败时返回默认名称
        return f"频道-{id}"

    def _extract_from_extinf(self, m3u8_content):
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

    def _extract_from_content_disposition(self, url):
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
        except Exception as e:
            logger.error(f"ChannelExtractor.extract_from_content_disposition error: {e}")

        return None

    def _detect_resolution(self, ts_url):
        """解析视频分辨率"""
        import av
        try:
            container = av.open(ts_url)
            video_stream = next(s for s in container.streams if s.type == 'video')
            return f"{video_stream.width}x{video_stream.height}"
        except Exception as e:
            logger.error(f"ChannelExtractor.detect_resolution error: {e}")
            return "unknown"

    def update_batch_live(self, threads, live_data, output_file, task_status) -> int:
        """批量更新直播频道信息 - 线程池版本"""
        total_count = len(live_data)
        success_counter = Counter()
        processed_counter = Counter()

        def process_item(args):
            category, subgenre, url = args
            channel_info = self.check_single(url, channel_name=subgenre)
            if channel_info:
                group_manager.add_group(category, channel_info)
                success_counter.increment()

            processed_counter.increment()
            with threading.Lock():
                task_status["progress"] = round(processed_counter.get_value() / total_count * 100, 2)
                task_status["processed"] = processed_counter.get_value()
                task_status["success"] = success_counter.get_value()

        optimal_threads = min(threads, os.cpu_count() * Constants.IO_INTENSITY_FACTOR + 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_threads) as executor:
            chunksize = max(1, total_count // (optimal_threads * 10))
            try:
                list(executor.map(process_item, live_data, chunksize=chunksize))
            except Exception as e:
                logger.error(f"Error during batch processing: {e}")
                raise

        self._write_data_to_file(output_file)
        return success_counter.get_value()

    def _write_data_to_file(self, file_path):
        """将分组管理器中的频道信息保存到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 写入数据
            with open(file_path, 'w', encoding='utf-8') as f:
                # 添加时间戳
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"# 频道数据导出时间: {timestamp}\n")
                group_manager.write_to_file(f)
            logger.info(f"channel data saved to file {file_path}")
        except Exception as e:
            logger.error(f"save data to file error: {e}")
