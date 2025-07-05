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
        self._convert_url = "http://107.174.95.154:25500/sub?target=clash"
        self._config = "https://gh-proxy.com/raw.githubusercontent.com/commis/sub-rule/main/clash/config/ACL4SSR_Online_Mini_MultiMode.ini"
        self._params = "insert=false&emoji=true&new_name=true"

        self._replace_empty_reg = r'[\U0001F1E6-\U0001F1FF]{2} |dafei\.de '
        self._pattern_filter = re.compile(r'^.*(v2ray-plugin).*$', re.MULTILINE)
        self._pattern_retain = re.compile(r'^.*(香港|新加坡).*$', re.MULTILINE)
        self._urls: Dict[str, str] = {
            "ssrsub_v2ray": "https://gh-proxy.com/raw.githubusercontent.com/ssrsub/ssr/master/V2Ray",
            "subsub_clash": "https://api.2c.lol/sub?target=v2ray&url=https%3A%2F%2Fraw.githubusercontent.com%2Fgo4sharing%2Fsub%2Fmain%2Fsub.yaml&insert=false"
        }

    def get_clash_subscribe(self, url_name: str) -> str:
        try:
            url = self._urls.get(url_name)
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            decoded_text = base64_decode(response.text)
            url_decode_text = url_decode(decoded_text)

            v2ray_urls = []
            for line in url_decode_text.splitlines():
                line = url_decode(line.strip())
                filtered = self._pattern_filter.match(line)
                retained = self._pattern_retain.match(line)
                if filtered or not retained:
                    continue

                line = re.sub(self._replace_empty_reg, '', line)
                v2ray_urls.append(line.replace(' ', '-'))

            return self._convert_to_clash('|'.join(v2ray_urls))
        except Exception as e:
            logger.error(f"get clash subscribe failed: {e}")

    def _convert_to_clash(self, ssrsub_text: str) -> str:
        url_encoded_config = url_encode(self._config)
        url_encoded_ssrsub_text = url_encode(ssrsub_text)
        url = f"{self._convert_url}&config=${url_encoded_config}&{self._params}&url=${url_encoded_ssrsub_text}"
        try:
            response = requests.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"convert ssrsub to clash failed: {e}")


subscribe_service = SubscribeService()
