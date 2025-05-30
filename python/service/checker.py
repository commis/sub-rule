import concurrent
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

import m3u8
import requests
from requests import Timeout

from core.constants import Constants
from core.logger_factory import LoggerFactory
from datastruct.channel_info import ChannelInfo
from datastruct.counter import Counter
from service import channel_manager
from service.group import group_manager

logger = LoggerFactory.get_logger(__name__)


class TimeoutException(Exception):
    """自定义超时异常"""
    pass


class ChannelExtractor:
    def __init__(self, url, start=0, size=1):
        self._url = url
        self._start = start
        self._size = size

    def check_single_with_timeout(
            self, url: str, cid=0,
            channel_name: Optional[str] = None,
            timeout: int = 60) -> Optional[ChannelInfo]:
        """带超时控制的频道检测方法"""
        try:
            timeout_event = threading.Event()
            timeout_event.clear()

            def check_with_timeout():
                try:
                    return self._check_single(url, cid, channel_name)
                except Exception as e:
                    logger.error(f"check_single error: {e}")
                    return None

            # 启动检测线程
            result = [None]
            exception = [None]
            thread = threading.Thread(target=lambda: result.__setitem__(0, check_with_timeout()))
            thread.daemon = True
            thread.start()

            thread.join(timeout)
            timeout_event.set()

            if thread.is_alive():
                logger.warning(f"Check for {url} timed out after {timeout} seconds")
                raise TimeoutException(f"Timeout checking {url}")

            if exception[0]:
                raise exception[0]
            return result[0]
        except:
            return None

    def _check_single(self, url, cid=0, channel_name=None) -> Optional[ChannelInfo]:
        # 第一阶段：基础验证
        m3u8_content = self._check_m3u8_url(url)
        if not m3u8_content:
            return None

        # 第二阶段：结构验证
        # is_valid, reason = self._check_m3u8_validity(m3u8_content)
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

    def _check_m3u8_url(self, url, timeout=5):
        """带超时的m3u8 URL检查"""
        try:
            # 明确设置连接和读取超时
            response = requests.get(url, timeout=(2, timeout - 2))
            if response.status_code == 200:
                return response.text
            return None
        except:
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

    def _check_ts_availability(self, ts_urls, base_url, timeout=5):
        """带超时和并发的TS片段检查"""
        success = 0
        tested_urls = []
        max_test_count = min(len(ts_urls), Constants.TS_SEGMENT_TEST_COUNT)

        # 使用线程池并发测试TS片段
        with ThreadPoolExecutor(max_workers=Constants.TS_SEGMENT_TEST_COUNT) as executor:
            futures = []
            start_time = time.time()

            for ts in ts_urls[:max_test_count]:
                full_url = ts if ts.startswith("http") else f"{base_url}/{ts}"
                futures.append(executor.submit(self._validate_ts, full_url, timeout=timeout / 2))

            # 带超时的结果处理
            for future in as_completed(futures, timeout=timeout):
                if time.time() - start_time > timeout:
                    break

                try:
                    if future.result():
                        success += 1
                        tested_urls.append(full_url)
                except Exception as e:
                    logger.debug(f"TS check error: {e}")

        if success == 0:
            return False, "all ts segments are not available", []
        return True, f"{success}/{max_test_count} segments are available", tested_urls

    def _validate_ts(self, url, timeout: float = 3) -> bool:
        """带超时的TS片段验证"""
        try:
            # 只获取头部信息，减少数据传输
            response = requests.head(url, timeout=(1, timeout - 1), allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"_validate_ts error: {e}")
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

    def _extract_channel_name(self, m3u8_content, id, url, timeout=3):
        """带超时的频道名称提取"""
        # 使用线程池处理可能耗时的正则匹配
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._extract_channel_name_worker, m3u8_content, id, url)
            try:
                # 等待提取完成或超时
                return future.result(timeout=timeout)
            except TimeoutException:
                logger.warning(f"Channel name extraction timed out for {url}")
                return f"频道-{id}"
            except Exception as e:
                logger.error(f"Channel name extraction error: {e}")
                return f"频道-{id}"

    def _extract_channel_name_worker(self, m3u8_content, id, url):
        """频道名称提取的实际工作函数"""
        # 方案1: 从EXTINF行提取
        channel_name = self._extract_from_extinf(m3u8_content)
        if channel_name:
            return channel_name

        # 方案2: 从Content-Disposition头提取 - 增加超时控制
        channel_name = self._extract_from_content_disposition(url, timeout=2)
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

    def _extract_from_content_disposition(self, url, timeout=2):
        """带超时的Content-Disposition提取"""
        try:
            response = requests.head(url, timeout=(1, timeout - 1), allow_redirects=True)
            if 'content-disposition' in response.headers:
                cd_header = response.headers['content-disposition']
                filename_match = re.findall("filename=(.+)", cd_header)
                if filename_match:
                    filename = filename_match[0].strip('";')
                    return os.path.splitext(filename)[0]
        except (Timeout, ConnectionError):
            pass
        except Exception as e:
            logger.error(f"extract_from_content_disposition error: {e}")

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

    def check_batch(self, threads, task_status) -> int:
        total_count = self._size
        success_count = 0
        processed_count = 0
        task_status_lock = threading.Lock()

        # 创建线程池，可根据需要调整
        optimal_threads = min(threads, os.cpu_count() * Constants.IO_INTENSITY_FACTOR + 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_threads) as executor:
            # 提交所有任务到线程池
            future_to_index = {
                executor.submit(
                    self.check_single_with_timeout,
                    url=self._url.format(i=index), cid=index, channel_name=None, timeout=30
                ): index
                for index in range(self._start, self._start + self._size)
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    channel_info = future.result()
                    if channel_info:
                        channel_manager.add_channel(channel_info)
                        success_count += 1
                except TimeoutException as te:
                    logger.warning(f"Timeout processing index {index}: {te}")
                except Exception as e:
                    logger.error(f"Error processing index {index}: {e}")
                finally:
                    with task_status_lock:
                        processed_count += 1
                        task_status["progress"] = round(processed_count / total_count * 100, 2)
                        task_status["processed"] = processed_count
                        task_status["success"] = success_count

        return success_count

    def update_batch_live(self, threads, output_file, task_status) -> int:
        """批量更新直播频道信息 - 最终优化版"""
        total_count = task_status["total"]
        success_counter = Counter()
        processed_counter = Counter()
        task_status_lock = threading.Lock()

        group_names = group_manager.get_groups()

        def process_url(task):
            channel_name, url, chanmel_map = task
            channel_info = self.check_single_with_timeout(url, channel_name=channel_name)
            try:
                if channel_info:
                    success_counter.increment()
                    return True
                else:
                    chanmel_map.remove_invalid_url(channel_name, url)
                    return False
            finally:
                with task_status_lock:
                    processed_counter.increment()
                    task_status["progress"] = round(processed_counter.get_value() / total_count * 100, 2)
                    task_status["processed"] = processed_counter.get_value()
                    task_status["success"] = success_counter.get_value()

        # 生成任务并立即处理
        optimal_threads = min(threads, os.cpu_count() * Constants.IO_INTENSITY_FACTOR + 1)
        with ThreadPoolExecutor(max_workers=optimal_threads) as executor:
            # 创建URL列表快照，避免并发修改
            def task_generator():
                actual_count = 0
                for group_name in group_names:
                    chanmel_map = group_manager.get_channels(group_name)
                    for channel_name in chanmel_map.get_channels():
                        urls = list(chanmel_map.get_urls(channel_name))
                        actual_count += len(urls)
                        for url in urls:
                            yield channel_name, url, chanmel_map
                # 验证实际任务数
                nonlocal total_count
                if actual_count != total_count:
                    logger.warning(f"Actual task count ({actual_count}) differs from expected total ({total_count})")
                    total_count = actual_count
                    task_status["total"] = total_count
                return actual_count

            # 提交所有任务
            futures = [executor.submit(process_url, task) for task in task_generator()]
            for future in as_completed(futures):
                future.result()

        # 最终状态验证
        final_processed = processed_counter.get_value()
        final_success = success_counter.get_value()
        logger.info(f"Final status: Processed={final_processed}, Total={total_count}, Success={final_success}")
        assert final_processed == total_count, f"Not all tasks were processed! {final_processed}/{total_count}"

        self._write_data_to_file(output_file)
        return final_success

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
