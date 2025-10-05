category_map = {
    '央视频道': '央视',
    '卫视频道': '卫视',
    '纪录频道': '纪录',
    '体育频道': '体育',
    '电影频道': '电影',
    '儿童频道': '儿童',
    "综艺频道": "综艺",
}

channel_map = {
    'CCTV1综合': 'CCTV1',
    'CCTV2财经': 'CCTV2',
    'CCTV3综艺': 'CCTV3',
    'CCTV4中文国际': 'CCTV4',
    'CCTV4美洲': 'CCTV4',
    'CCTV4欧洲': 'CCTV4',
    'CCTV5体育': 'CCTV5',
    'CCTV5+体育赛事': 'CCTV5+',
    'CCTV6电影': 'CCTV6',
    'CCTV7国防军事': 'CCTV7',
    'CCTV8电视剧': 'CCTV8',
    'CCTV9纪录': 'CCTV9',
    'CCTV10科教': 'CCTV10',
    'CCTV11戏曲': 'CCTV11',
    'CCTV12社会与法': 'CCTV12',
    'CCTV13新闻': 'CCTV13',
    'CCTV14少儿': 'CCTV14',
    'CCTV15音乐': 'CCTV15',
    'CCTV16财经': 'CCTV16',
    'CCTV17农业农村': 'CCTV17',
    'CGTN外语纪录': 'CGTN纪录',
    'CGTN西班牙语': 'CGTN西语',
    'CGTN阿拉伯语': 'CGTN阿语',
}


class Const:

    @staticmethod
    def get_category(category_name: str) -> str:
        return category_map.get(category_name, category_name)

    @staticmethod
    def get_channel(channel_name: str) -> str:
        return channel_map.get(channel_name, channel_name)
