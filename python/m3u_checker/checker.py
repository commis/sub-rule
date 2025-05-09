import concurrent.futures
import time

import requests


def check_channel(url, timeout=10):
    """检查单个频道是否可达"""
    try:
        start_time = time.time()
        response = requests.head(url, timeout=timeout)
        end_time = time.time()

        return {
            'reachable': True,
            'latency': end_time - start_time,
            'status_code': response.status_code,
            'message': '成功'
        }
    except requests.exceptions.Timeout:
        return {
            'reachable': False,
            'latency': timeout,
            'status_code': None,
            'message': '连接超时'
        }
    except requests.exceptions.ConnectionError:
        return {
            'reachable': False,
            'latency': None,
            'status_code': None,
            'message': '连接错误'
        }
    except Exception as e:
        return {
            'reachable': False,
            'latency': None,
            'status_code': None,
            'message': str(e)
        }


def check_channels(urls, timeout=10, max_workers=10):
    """并发检查多个频道"""
    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有检查任务
        future_to_url = {executor.submit(check_channel, url, timeout): url for url in urls}

        # 收集结果
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                results[url] = {
                    'reachable': False,
                    'latency': None,
                    'status_code': None,
                    'message': f'检查时出错: {str(e)}'
                }

    return results
