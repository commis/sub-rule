import re
from typing import Dict

import requests

from core.constants import Constants
from core.logger_factory import LoggerFactory
from core.singleton import singleton
from utils.base64_util import base64_decode
from utils.url_util import url_decode, url_encode

logger = LoggerFactory.get_logger(__name__)


@singleton
class SubscribeService:

    def __init__(self):
        self._sub_url = "http://107.174.95.154:25500/sub"
        self._config = "https://raw.githubusercontent.com/commis/sub-rule/main/clash/config/ACL4SSR_Online_Mini_MultiMode.ini"
        self._params = "clash.dns=1&insert=false&emoji=true&new_name=true"

        self._pattern_2empty = r'dafei\.de |-[A-Za-z\s,\. ]+- '
        # self._replace_empty_reg = r'[\U0001F1E6-\U0001F1FF]{2} |dafei\.de '
        # self._regex_filter = re.compile(r'^.*(v2ray-plugin).*$', re.MULTILINE)
        self._regex_filter = re.compile(r'^.*(中国|日本).*$', re.MULTILINE)
        self._urls: Dict[str, str] = {
            "ssrsub": "https://raw.githubusercontent.com/ssrsub/ssr/master/Clash.yaml",
            "subsub": "https://raw.githubusercontent.com/go4sharing/sub/main/sub.yaml"
        }

    def _convert_to_v2ray(self, input_url: str) -> str:
        url_encoded_input_url = url_encode(input_url)
        url = f"{self._sub_url}?target=v2ray&url={url_encoded_input_url}"
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            decoded_text = base64_decode(response.text)
            return decoded_text
        except Exception as e:
            logger.error(f"convert ssrsub to clash failed: {e}")

    def _convert_to_clash(self, ssrsub_text: str) -> str:
        url_encoded_config = url_encode(self._config)
        url_encoded_ssrsub_text = url_encode(ssrsub_text)
        url = f"{self._sub_url}?target=clash&url=${url_encoded_ssrsub_text}&config={url_encoded_config}&{self._params}"
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            lines = response.text.splitlines()
            filtered_lines = [self._replace(line) for line in lines if self._should_include_line(line, False)]
            return '\n'.join(filtered_lines)
        except Exception as e:
            logger.error(f"convert ssrsub to clash failed: {e}")

    def _should_include_line(self, line: str, invert: bool = False) -> bool:
        """判断行是否应被包含在结果中"""
        return (self._regex_filter.search(line) is None) ^ invert

    def _replace(self, line: str) -> str:
        """替换数据行"""
        return re.sub(self._pattern_2empty, '', line)

    def get_clash_subscribe(self, url_name: str) -> str:
        try:
            url = self._urls.get(url_name)
            decoded_text = self._convert_to_v2ray(url)
            sub_url_text = re.sub(re.compile(r'\n'), '|', decoded_text)
            return self._convert_to_clash(sub_url_text)
        except Exception as e:
            logger.error(f"get clash subscribe failed: {e}")

    # def get_v2ray_subscribe(self, url_name: str) -> str:
    #     try:
    #         url = self._urls.get(url_name)
    #         response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
    #         response.raise_for_status()
    #         decoded_text = base64_decode(response.text)
    #         url_decode_text = url_decode(decoded_text)
    #
    #         v2ray_urls = []
    #         for line in url_decode_text.splitlines():
    #             line = url_decode(line.strip())
    #             filtered = self._regex_filter.match(line)
    #             retained = self._regex_retain.match(line)
    #             if filtered or not retained:
    #                 continue
    #
    #             line = re.sub(self._replace_empty_reg, '', line)
    #             v2ray_urls.append(line.replace(' ', '-'))
    #
    #         return self._convert_to_clash('|'.join(v2ray_urls))
    #     except Exception as e:
    #         logger.error(f"get clash subscribe failed: {e}")


subscribe_service = SubscribeService()
