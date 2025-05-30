import re

import requests
from bs4 import BeautifulSoup

from core.constants import Constants
from core.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def parse_channel_data(text_data, is_filter=False) -> list:
    """
    将用户提供的频道数据文本解析为指定格式的元组列表
    :return: 解析后的元组列表，格式为 [(类别, 子类型, URL), ...]
    """
    from service import category_manager

    data = []
    current_category = None
    lines = [line.strip() for line in text_data.split('\n') if line.strip()]

    # 合并正则：移除表情符号、逗号、#genre#和多余空格
    clean_pattern = re.compile(
        r'[\U0001F000-\U0001FFFF\U00002500-\U00002BEF\U00002E00-\U00002E7F\U00003000-\U00003300,#genre#\s]+')

    for line in lines:
        # 识别类别行（以#genre#结尾）
        if '#genre#' in line:
            category_part = clean_pattern.sub(' ', line).strip()
            if category_part:
                current_category = category_part
            continue

        if current_category:
            # 过滤掉不需要找的分类
            if is_filter and category_manager.is_not_exist(current_category):
                continue

            parts = line.split(',', 1)
            if len(parts) < 2:
                continue

            subgenre, url = [p.strip() for p in parts]
            if url:
                data.append((current_category, subgenre, url))

    return data


def parse_sitemap_data(sitemap_url) -> list:
    data = []
    try:
        response = requests.get(sitemap_url, timeout=Constants.REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'xml')
        urls = []
        for loc in soup.find_all('loc'):
            url = loc.text.strip()
            if url.endswith(".txt"):
                urls.append(url)

        content = ''
        for url in urls:
            text = __get_remote_url_data(url)
            if text:
                content += text
        data = parse_channel_data(content, True)
    except Exception as e:
        logger.error(f"parse sitemap data failed: {e}")

    return data


def __get_remote_url_data(url):
    try:
        response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
        response.raise_for_status()
        return f"{response.text}\n"
    except Exception as e:
        logger.error(f"obtain remote url data failed: {e}")
        return None
