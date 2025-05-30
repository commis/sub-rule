# constants.py
class Constants:
    """项目公共常量类，包含所有业务需要的常量定义"""

    # 网络请求相关常量
    REQUEST_TIMEOUT = 10  # 网络请求超时时间（秒）

    # 线程池相关常量
    IO_INTENSITY_FACTOR = 4  # 可在2-8之间调整

    # M3U8解析相关常量
    TS_SEGMENT_TEST_COUNT = 3  # 测试TS片段数量
    TS_HEADER_CHECK_BYTES = 1024  # TS头部检查字节数

    # 测速相关常量
    SPEED_TEST_BYTES = 512  # 测速下载字节数
    SPEED_TEST_CHUNK_SIZE = 1024  # 测速分块大小
