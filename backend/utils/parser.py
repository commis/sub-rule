import requests
from bs4 import BeautifulSoup

from core.constants import Constants
from core.logger_factory import LoggerFactory
from services import channel_manager, category_manager

logger = LoggerFactory.get_logger(__name__)


class Parser:
    _live_url = "http://107.174.95.154/tvbox/live.txt"

    @staticmethod
    def get_channel_data(text_data: str) -> list:
        """
        将用户提供的频道数据文本解析为 [(类别, 子类型, URL), ...] 格式的元组列表
        """

        def generate_channels():
            category_stack = None
            for line in (line.strip() for line in text_data.splitlines() if line.strip() and not line.startswith('#')):
                if line.endswith('#genre#'):
                    category_stack = None
                    category = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line[:-7]).strip()
                    if category:
                        category_stack = category
                    continue

                if category_stack:
                    try:
                        subgenre, url = line.split(',', 1)
                        subgenre = subgenre.strip()
                        url = url.strip()
                        if not url:
                            continue
                        current_category = (
                            category_manager.get_category_name(subgenre)
                            if subgenre.startswith('CCTV')
                            else category_stack
                        )
                        yield current_category, subgenre, url
                    except ValueError:
                        continue

        return list(generate_channels())

    def load_sitemap_data(cls, url: str):
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            for loc in soup.find_all('loc'):
                url = loc.text.strip()
                if not url.endswith(".txt"):
                    continue
                cls._get_remote_url_data(url)

            # 处理自建频道
            cls._get_remote_url_data(cls._live_url)
            channel_manager.sort()
        except Exception as e:
            logger.error(f"parse sitemap data failed: {e}")

    def _get_remote_url_data(cls, url):
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            cls.load_channel_data(response.text.strip())
        except Exception as e:
            logger.error(f"access remote url data failed: {e}")

    @staticmethod
    def load_channel_data(text_data):
        from services import category_manager

        category_stack = None
        for line in (line.strip() for line in text_data.splitlines() if line.strip() and not line.startswith('#')):
            if line.endswith('#genre#'):
                category_stack = None
                category = Constants.CATEGORY_CLEAN_PATTERN.sub(' ', line).strip()
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
