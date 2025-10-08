#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @time   : 10/8/25
# @author : Brian
# @license: (C) Copyright 2022-2026
import argparse
import base64
import json

import requests


def get_tv_json(mark="**", url: str = "http://ok321.top/tv", output: str = "./index.json"):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tv_data = response.text.strip()

        # 分割数据并解码
        json_data = base64.b64decode(tv_data.split(mark, 1)[1]).decode()

        # 替换特定字符串为空
        target_str = "http://127.0.0.1:9978/proxy?do=live&url="
        json_data = json_data.replace(target_str, "")

        data = json.loads(json_data)
        new_items = [
            {
                "name": "我的电视",
                "type": 0,
                "url": "http://107.174.95.154/tvbox/json/result.txt",
                "playerType": 2
            }, {
                "name": "广播电台",
                "type": 0,
                "url": "http://107.174.95.154/tvbox/json/music.txt",
                "playerType": 1,
                "timeout": 10
            }, {
                "name": "AI直播",
                "type": 0,
                "url": "http://107.174.95.154/tvbox/json/interface.txt",
                "playerType": 2,
                "timeout": 10
            }
        ]

        # 在lives数组最前面添加新数据
        if "lives" in data:  # 新数据在前，原有数据在后
            filtered_lives = [
                item for item in data["lives"]
                if "name" in item and item["name"].lower() != "ai直播"
            ]
            data["lives"] = new_items + filtered_lives
        else:
            data["lives"] = new_items

        json_data = json.dumps(data, ensure_ascii=False, indent=2)

        # 保存到文件
        with open(output, 'w', encoding='utf-8') as f:
            f.write(json_data)

        print(f"success save tv data to {output}")
    except Exception as e:
        print(f"parse tv data failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='处理TV JSON数据的脚本')
    parser.add_argument('--url', type=str, help='数据源URL地址', default="http://ok321.top/tv")
    parser.add_argument('--output', type=str, help='输出文件路径', default="./index.json")

    args = parser.parse_args()
    get_tv_json(url=args.url, output=args.output)
