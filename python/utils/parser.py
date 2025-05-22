import re


def parse_channel_data(text_data):
    """
    将用户提供的频道数据文本解析为指定格式的元组列表
    :param text_data: 包含频道数据的文本字符串
    :return: 解析后的元组列表，格式为 [(类别, 子类型, URL), ...]
    """
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
            parts = line.split(',', 1)
            if len(parts) < 2:
                continue

            subgenre, url = [p.strip() for p in parts]
            if url:
                data.append((current_category, subgenre, url))

    return data
