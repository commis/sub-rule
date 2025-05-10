#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @time   : 5/6/25
# @author : Brian
# @license: (C) Copyright 2022-2026
import argparse
import contextlib
import os

import av
import m3u8
import requests


class ChannelInfo:
    def __init__(self, id, url):
        self.id = id
        self.url = url
        self.channel_name = None

    def set_channel_name(self, channel_name):
        self.channel_name = channel_name

    def _channel_name(self):
        return self.channel_name or f"频道{self.id}"

    def get_txt(self):
        return f"{self._channel_name()},{self.url}"

    def get_m3u(self):
        return f"#EXTINF:-1,{self._channel_name()}\n{self.url}"


class ChannelExtractor:
    def __init__(self, url, start, size, path=None):
        self.template_url = url
        self.start = start
        self.size = size
        self.dir = path or os.getcwd()
        self.results = []

    def check_m3u8_url(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except requests.RequestException:
            return None

    def extract_ts_urls(self, m3u8_content):
        m3u8_obj = m3u8.loads(m3u8_content)
        return m3u8_obj.segments.uri

    def download_ts(self, ts_url, ts_filename):
        try:
            response = requests.get(ts_url)
            if response.status_code == 200:
                with open(ts_filename, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except requests.RequestException:
            return False

    def extract_channel_stream(self, ts_filename):
        try:
            container = av.open(ts_filename)
            for stream in container.streams:
                print(f"Stream type: {stream.type}, Codec: {stream.codec_context.codec.name}")
            return "Extracted some basic stream info"
        except Exception as e:
            print(f"Error extracting channel info: {e}")
            return None
        finally:
            if os.path.exists(ts_filename):
                os.remove(ts_filename)

    def extract_channel_name(self, m3u8_content):
        lines = m3u8_content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('#EXTINF'):
                parts = line.split(',')
                if len(parts) > 1:
                    return parts[1]
        return None

    def run(self):
        for index in range(self.start, self.start + self.size):
            result = ChannelInfo(index, self.template_url.format(i=index))
            m3u8_content = self.check_m3u8_url(result.url)
            if m3u8_content:
                result.set_channel_name(self.extract_channel_name(m3u8_content))
                ts_urls = self.extract_ts_urls(m3u8_content)
                if len(ts_urls) > 0:
                    self.results.append(result)
                # for i, ts_url in enumerate(ts_urls):
                #     if not ts_url.startswith('http'):
                #         base = result.url.rsplit('/', 1)[0]
                #         ts_url = f"{base}/{ts_url}"
                #     ts_filename = f"temp_{index}_{i}.ts"
                #     if self.download_ts(ts_url, ts_filename):
                #         channel_info = self.extract_channel_stream(ts_filename)
                #         if channel_info:
                #             print(f"有效地址: {result.url}, TS片段: {ts_url}, 频道信息: {channel_info}")
                #         else:
                #             print(f"有效地址: {result.url}, TS片段: {ts_url}, 未找到频道信息")
                #     else:
                #         print(f"无效TS地址: {ts_url}")
            else:
                print(f"无效m3u8地址: {result.url}")

    def dump_results(self):
        try:
            with contextlib.ExitStack() as stack:
                txt_file = stack.enter_context(open(f"{self.dir}/iptv_checker.txt", 'w', encoding='utf-8'))
                m3u_file = stack.enter_context(open(f"{self.dir}/iptv_checker.m3u", 'w', encoding='utf-8'))
                for i, item in enumerate(self.results, start=1):
                    txt_file.write(f"{item.get_txt()}\n")
                    m3u_file.write(f"{item.get_m3u()}\n")
        except Exception as e:
            print(f"写入文件时出错: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Channel Extractor')
    parser.add_argument('base_url', type=str, help='Base URL')
    parser.add_argument('index', type=int, help='Start index')
    parser.add_argument('number', type=int, help='Number')
    parser.add_argument('--output', type=str, default=None, help='Path to output file')

    try:
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
    else:
        extractor = ChannelExtractor(args.base_url, args.index, args.number, args.output)
        extractor.run()
        extractor.dump_results()
