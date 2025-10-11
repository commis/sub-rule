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
    'CCTV1': 'CCTV1综合',
    'CCTV2': 'CCTV2财经',
    'CCTV3': 'CCTV3综艺',
    'CCTV4': 'CCTV4中文国际',
    'CCTV5': 'CCTV5体育',
    'CCTV5+': 'CCTV5+体育赛事',
    'CCTV6': 'CCTV6电影',
    'CCTV7': 'CCTV7国防军事',
    'CCTV8': 'CCTV8电视剧',
    'CCTV9': 'CCTV9纪录',
    'CCTV10': 'CCTV10科教',
    'CCTV11': 'CCTV11戏曲',
    'CCTV12': 'CCTV12社会与法',
    'CCTV13': 'CCTV13新闻',
    'CCTV14': 'CCTV14少儿',
    'CCTV15': 'CCTV15音乐',
    'CCTV16': 'CCTV16奥林匹克',
    'CCTV17': 'CCTV17农业农村',
    'CGTN纪录': 'CGTN外语纪录',
    'CGTN西语': 'CGTN西班牙语',
    'CGTN阿语': 'CGTN阿拉伯语',
    '中国农林卫视': '陕西农林卫视',
    '体育休闲': '江苏体育休闲'
}


class Const:

    @staticmethod
    def get_category(category_name: str) -> str:
        return category_map.get(category_name, category_name)

    @staticmethod
    def get_channel(channel_name: str) -> str:
        return channel_map.get(channel_name, channel_name).replace('频道', '')
