import time

import requests

from helper_56tool import 灵动爬虫, ParseUrlError

CRAWLER_HOST = 'http://localhost:8000'

# external_api.py
def 获取字幕任务():
    url = f'{CRAWLER_HOST}/docshare/tasks?task_name=视频字幕'
    data = requests.get(url).json()
    return data

def 更新字幕数据(task_id, txt):
    url = f'{CRAWLER_HOST}/docshare/tasks?task_name=视频字幕'
    data = {'id': task_id, 'task_name': '视频字幕', 'task_value': txt}
    data = requests.post(url, data).json()
    return data

# 功能

def 获取字幕():
    爬虫 = 灵动爬虫()
    try_times = 3
    while try_times:
        task = 获取字幕任务()
        if not task:
            time.sleep(1)
            break
        # url = task['视频链接']
        url = task['分享链接']


        try:
            txt = 爬虫.提取视频文案(url)
            更新字幕数据(task['id'], txt)
            try_times = 3
        except ParseUrlError:
            print('获取文案异常')
            try_times -= 1
            time.sleep(1)


