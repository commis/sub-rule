class ChannelInfo:
    def __init__(self, id, url):
        self.id = id
        self.url = url
        self.name = None
        self.speed = 0  # 单位：KB/s
        self.resolution = "未知"

    def set_channel_name(self, channel_name):
        if channel_name:
            self.name = channel_name.strip()

    def set_speed(self, speed):
        self.speed = round(speed, 1)

    def set_resolution(self, res):
        self.resolution = res

    def __channel_name(self):
        return self.name or f"频道-{self.id}"

    def get_txt(self):
        return f"{self.__channel_name()},{self.url}"

    def get_m3u(self):
        return f"#EXTINF:-1,{self.__channel_name()}\n{self.url}"

    def get_all(self) -> str:
        return (f"{self.get_txt()}\n\n"
                f"==================\n"
                f"{self.get_m3u()}")
