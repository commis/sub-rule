import requests
from bs4 import BeautifulSoup

from core.constants import Constants
from core.logger_factory import LoggerFactory
from services import channel_manager, category_manager

logger = LoggerFactory.get_logger(__name__)


class Parser:
    _live_url = "http://107.174.95.154/tvbox/json/live.txt"

    @staticmethod
    def get_channel_data(text_data: str) -> list:
        """
        将用户提供的频道数据文本解析为 [(类别, 子类型, URL), ...] 格式的元组列表
        """
        category_stack = None
        special_category = None
        channel_list = []

        for line in text_data.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.endswith('#genre#'):
                category = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line[:-7]).strip()
                category_stack = category if category else None
                special_category = None
                continue

            if category_stack:
                parts = line.split(',', 1)
                if len(parts) != 2:
                    continue
                channel_name, url = [p.strip() for p in parts]
                if not url:
                    continue

                category_info = category_manager.get_category_object(channel_name, special_category)
                category_name = category_info.get('name')
                if not category_manager.is_exclude(category_info, channel_name):
                    channel_list.append((category_name, channel_name, url))

        return channel_list

    def load_sitemap_data(cls, url: str):
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            for loc in soup.find_all('loc'):
                url = loc.text.strip()
                if not url.endswith("iptv4.txt"):
                    continue
                cls._get_remote_url_data(url, True)

            # 处理自建频道
            cls._get_remote_url_data(cls._live_url)
            channel_manager.sort()
        except Exception as e:
            logger.error(f"parse sitemap data failed: {e}")

    def _get_remote_url_data(cls, url, use_ignore=False):
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            cls.load_channel_data(response.text.strip(), use_ignore)
        except Exception as e:
            logger.error(f"access remote url data failed: {e}")

    @staticmethod
    def load_channel_data(text_data, use_ignore: bool = False):
        from services import category_manager

        category_stack = None
        for line in (line.strip() for line in text_data.splitlines() if line.strip() and not line.startswith('#')):
            if line.endswith('#genre#'):
                category_stack = None
                category = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line).strip()
                if use_ignore and category_manager.is_ignore(category):
                    continue
                if category and category_manager.exists(category):
                    category_stack = category
                continue

            if category_stack:
                # 解析频道信息
                try:
                    subgenre, url = line.split(',', 1)
                    subgenre, url = subgenre.strip(), url.strip()
                    if url:
                        channel_manager.add_channel(category_stack, subgenre, url)
                except ValueError:
                    continue
