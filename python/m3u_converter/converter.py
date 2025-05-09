def convert(m3u_file, output_format='json'):
    """转换 M3U 文件到指定格式"""
    # 读取 M3U 文件内容
    content = m3u_file.read().decode('utf-8')

    # 解析 M3U 文件
    channels = parse_m3u(content)

    # 根据输出格式返回结果
    if output_format == 'json':
        return channels
    elif output_format == 'csv':
        return convert_to_csv(channels)
    else:
        return convert_to_plain_text(channels)


def parse_m3u(content):
    """解析 M3U 文件内容，提取频道信息"""
    lines = content.strip().split('\n')
    channels = []
    current_channel = None

    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 解析频道信息
            info = line[8:].strip()
            parts = info.split(',', 1)
            duration = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else ''

            current_channel = {
                'duration': duration,
                'name': name,
                'url': ''
            }
        elif line.startswith('#'):
            # 忽略其他元数据行
            continue
        elif current_channel and line:
            # 这是频道的 URL
            current_channel['url'] = line
            channels.append(current_channel)
            current_channel = None

    return channels


def convert_to_csv(channels):
    """将频道列表转换为 CSV 格式"""
    import io
    import csv

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name', 'duration', 'url'])
    writer.writeheader()
    writer.writerows(channels)

    output.seek(0)
    return output


def convert_to_plain_text(channels):
    """将频道列表转换为纯文本格式"""
    if not channels:
        return "没有找到频道"

    lines = []
    for i, channel in enumerate(channels, 1):
        lines.append(f"频道 #{i}:")
        lines.append(f"  名称: {channel['name']}")
        lines.append(f"  时长: {channel['duration']}")
        lines.append(f"  URL: {channel['url']}")
        lines.append("")  # 空行分隔每个频道

    return "\n".join(lines)
