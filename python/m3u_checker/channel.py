class ChannelInfo:
    def __init__(self, id, url):
        self.id = id
        self.url = url
        self.channel_name = None

    def set_channel_name(self, channel_name):
        self.channel_name = channel_name

    def __channel_name(self):
        return self.channel_name or f"频道-{self.id}"

    def get_txt(self):
        return f"{self.__channel_name()},{self.url}"

    def get_m3u(self):
        return f"#EXTINF:-1,{self.__channel_name()}\n{self.url}"

    def get_all(self) -> str:
        return (f"{self.get_txt()}\n\n"
                f"==================\n"
                f"{self.get_m3u()}")
