import requests
from bs4 import BeautifulSoup

from core.constants import Constants
from core.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def parse_channel_data(text_data) -> list:
    """
    将用户提供的频道数据文本解析为指定格式的元组列表
    :return: 解析后的元组列表，格式为 [(类别, 子类型, URL), ...]
    """
    data = []
    current_category = None

    # 使用生成器逐行处理文本数据，避免一次性加载所有行到内存
    def line_generator():
        start = 0
        while True:
            end = text_data.find('\n', start)
            if end == -1:
                if start < len(text_data):
                    yield text_data[start:].strip()
                break
            line = text_data[start:end].strip()
            if line:
                yield line
            start = end + 1

    for line_text in line_generator():
        # 识别类别行（以#genre#结尾）
        if '#genre#' in line_text:
            category_part = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line_text).strip()
            if category_part:
                current_category = category_part
            continue

        if current_category:
            parts = line_text.split(',', 1)
            if len(parts) < 2:
                continue

            subgenre, url = [p.strip() for p in parts]
            if url:
                data.append((current_category, subgenre, url))

    return data


def parse_sitemap_data(sitemap_url) -> int:
    total_count = 0
    try:
        response = requests.get(sitemap_url, timeout=Constants.REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'xml')
        urls = []
        for loc in soup.find_all('loc'):
            url = loc.text.strip()
            if url.endswith(".txt"):
                urls.append(url)

        for url in urls:
            text = _get_remote_url_data(url)
            if text:
                total_count += _parse_sitemap_channel_data(text)
    except Exception as e:
        logger.error(f"parse sitemap data failed: {e}")

    return total_count


def _get_remote_url_data(url):
    try:
        response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
        response.raise_for_status()
        return f"{response.text}\n"
    except Exception as e:
        logger.error(f"obtain remote url data failed: {e}")
        return None


def _parse_sitemap_channel_data(text_data) -> int:
    """
    将用户提供的频道数据文本解析并存储GroupManager中
    """
    from service import category_manager
    from service.group import group_manager
    current_category = None
    total_data_count = 0

    # 使用生成器逐行处理文本数据，避免一次性加载所有行到内存
    def line_generator():
        start = 0
        while True:
            end = text_data.find('\n', start)
            if end == -1:
                if start < len(text_data):
                    yield text_data[start:].strip()
                break
            line = text_data[start:end].strip()
            if line:
                yield line
            start = end + 1

    for line_text in line_generator():
        # 识别类别行（以#genre#结尾）
        if '#genre#' in line_text:
            category_part = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line_text).strip()
            if category_part:
                current_category = category_part
            continue

        if current_category:
            parts = line_text.split(',', 1)
            if len(parts) < 2 or category_manager.is_not_exist(current_category):
                continue

            subgenre, url = [p.strip() for p in parts]
            if url:
                group_manager.add_group(current_category, subgenre, url)
                total_data_count += 1

    return total_data_count
