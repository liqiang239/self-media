# encoding: utf-8
"""
Created on 2015年8月14日

@author: root
"""
import platform
import subprocess
import time
import os

from django.core.management.base import BaseCommand
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException
import urllib3

from base.models import 头条热榜新闻, 处理记录, 评论, 回复
from helper_subtitle import 获取字幕

from helper_toutiao import 头条爬虫

from simple_news.models import 头条新闻

from docshare.models import 抖音医生号, 抖音视频
import requests

SERVICE_URL = "http://192.168.0.144:8000/"


def touch(file_path):
    """创建一个空文件，类似于 Linux 的 touch 命令"""
    with open(file_path, "a"):
        pass


class 文件信号器(object):
    def __init__(self, file_path):
        self._file_path = file_path

    def 创建(self):
        touch(self._file_path)

    def 是否存在(self):
        return os.path.lexists(self._file_path)

    def 删除(self):
        if self.是否存在():
            os.remove(self._file_path)

    def 启动(self):
        self.创建()

    def 关闭(self):
        self.删除()


# 爬虫运行信号 = 文件信号器(os.path.join(BASE_DIR, "running"))
# 爬虫停止信号 = 文件信号器(os.path.join(BASE_DIR, "stop"))


def kill_chrome():
    cmd = ""
    system = platform.system()
    if system == "Windows":
        cmd = "taskkill /F /IM chrome.exe"
    elif system == "Linux":
        cmd = "killall -9 chrome"
    process = subprocess.Popen(
        cmd,
        # encoding='utf8',
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process.communicate()
    头条爬虫.清除单例()


def 清理老数据():
    头条热榜新闻.删除所有n天前的新闻(10)
    评论.删除所有n天前的评论(10)
    回复.删除所有n天前的回复(10)


# def 爬取一次(seconds=3600, headless=False, driver_path=None, user_data_dir=None):
#     old = time.time()
#     print("@" * 20, "准备重启进程...", "@" * 20)
#     爬虫 = None
#     while 1:
#         try:
#             if 爬虫 is None:
#                 爬虫 = 头条爬虫(
#                     headless=headless,
#                     driver_path=driver_path,
#                     user_data_dir=user_data_dir,
#                 )

#             if time.time() - old >= seconds:
#                 爬虫.quit()
#                 break

#             if 头条热榜新闻.是否需要刷新(间隔分钟数=5):
#                 if 头条热榜新闻.刷新热榜(爬虫):
#                     处理记录.刷新n小时记录(8)
#                 else:
#                     print("刷新热榜失败")
#                     kill_chrome()
#                     break
#                 continue

#             t = 处理记录.得到第一个需要处理的记录()
#             if t is not None:
#                 print(t, "开始爬取评论。。。")
#                 t.最新.爬取评论(爬虫)
#         except urllib3.exceptions.MaxRetryError as e:
#             print("$" * 30)
#             print(e)
#             print("$" * 30)
#             kill_chrome()
#             break
#         except SessionNotCreatedException as e:
#             print("$" * 30)
#             print(e)
#             print("$" * 30)
#             kill_chrome()
#             break
#         except TimeoutException as e:
#             print("$" * 30)
#             print(e)
#             print("$" * 30)
#             kill_chrome()
#             break


def 为第一个需要下载抖音视频的记录创建任务():
    t = 处理记录.得到第一个需要下载抖音视频的记录()
    if t is not None:
        print(t, "开始下载抖音视频。。。")
        t.创建抖音视频下载任务(头条爬虫.得到爬虫单例())


def 爬取一次():
    if 头条热榜新闻.是否需要刷新分类热榜(间隔分钟数=60):
        if 头条热榜新闻.刷新分类热榜(头条爬虫.得到爬虫单例()):
            处理记录.刷新n小时记录(8)
        else:
            print("刷新分类热榜失败")
            kill_chrome()
    elif 头条热榜新闻.是否需要刷新(间隔分钟数=5):
        if 头条热榜新闻.刷新热榜(头条爬虫.得到爬虫单例()):
            处理记录.刷新n小时记录(8)
        else:
            print("刷新热榜失败")
            kill_chrome()
    else:
        t = 处理记录.得到第一个需要处理的记录()
        if t is not None:
            print(t, "开始爬取评论。。。")
            t.最新.爬取评论(头条爬虫.得到爬虫单例())

def 爬取一次新版本():
    # 头条新闻.是否需要刷新分类热榜
    # print(头条新闻.是否需要刷新())
    # news = 头条新闻.得到最早需爬取评论的新闻()
    # print(news)

    if 头条新闻.是否需要刷新(间隔分钟数=5):
        if not 头条新闻.刷新分类热榜(头条爬虫.得到爬虫单例()):
            print("刷新分类热榜失败")
            kill_chrome()
        else:
            print("刷新热榜成功")
    else:
        news = 头条新闻.得到最早需爬取评论的新闻()
        if news is not None:
            print(news, "开始爬取评论。。。")
            news.爬取评论(头条爬虫.得到爬虫单例())


# def 爬取一次_老版本():
#     if 头条热榜新闻.是否需要刷新(间隔分钟数=5):
#         if 头条热榜新闻.刷新热榜(头条爬虫.得到爬虫单例()):
#             处理记录.刷新n小时记录(8)
#         else:
#             print("刷新热榜失败")
#             kill_chrome()
#     else:
#         t = 处理记录.得到第一个需要处理的记录()
#         if t is not None:
#             print(t, "开始爬取评论。。。")
#             t.最新.爬取评论(头条爬虫.得到爬虫单例())



def 单步运行():
    # 任务表.安全处理第一条任务()
    # 快讯制作.自动生成快讯()
    爬取一次新版本()
    # 为第一个需要下载抖音视频的记录创建任务()


def 运行所有任务(seconds=3600):
    kill_chrome()
    old = time.time()
    print("@" * 20, "准备重启进程...", "@" * 20)
    # 爬虫 = None

    # 上一次清理时间 = time.time()

    while 1:
        try:

            # if time.time() - 上一次清理时间 >= 24 * 3600:
            #     清理老数据()
            #     上一次清理时间 = time.time()
            #     continue

            if time.time() - old >= seconds:
                头条爬虫.清除单例()
                old = time.time()
                continue
            单步运行()

        except urllib3.exceptions.MaxRetryError as e:
            print("$" * 30)
            print(e)
            print("$" * 30)
            kill_chrome()
            break
        except SessionNotCreatedException as e:
            print("$" * 30)
            print(e)
            print("$" * 30)
            kill_chrome()
            break
        except TimeoutException as e:
            print("$" * 30)
            print(e)
            print("$" * 30)
            kill_chrome()
            break


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("--headless", action="store_true", default=False)
        # parser.add_argument("--driver_path", nargs="?", default=None, type=str)
        # parser.add_argument("--user_data_dir", nargs="?", default=None, type=str)

        # parser.add_argument("--爬", action="store_true", default=False)

        parser.add_argument("--testit", action="store_true", default=False)

        parser.add_argument("--step", action="store_true", default=False)

        parser.add_argument("--run", action="store_true", default=False)
        
        parser.add_argument("--爬取所有医生号的所有视频", action="store_true", default=False)
        parser.add_argument("--get_subtitle", action="store_true", default=False)

    def handle(self, *args, **options):
        if options.get("testit"):
            # import requests
            # r = requests.post("http://localhost:9000/base/pull")
            # print(r.json())
            # obj = 处理记录.objects.last()
            # obj.创建抖音视频下载任务(爬虫)
            # 为第一个需要下载抖音视频的记录创建任务()
            # 任务表.安全处理第一条任务()

            # import requests

            # url = "http://localhost:9000/api/fast_news_prodcast"
            # data = {
            #     "id": 1,
            #     "处理记录id": 213,
            #     "音频链接": "https://www.toutiao.com/trending/7481644231565017115/",
            # }
            # r = requests.post(url, data=data).json()
            # # r = requests.post("http://localhost:9000/api/fast_news_prodcast")
            # print(r)
            # 爬虫 = 头条爬虫.得到爬虫单例()
            
            # 头条新闻.刷新分类热榜(爬虫)
            # news = 头条新闻.得到最早需爬取评论的新闻()
            # news.爬取评论(头条爬虫.得到爬虫单例())
            # obj = 抖音医生号.objects.first()
            # obj.全部抓取所有视频()
            抖音视频.清理所有状态()
            # url = "http://localhost:7000/docshare/tasks"
            url = "http://localhost:7000/simple_news/tasks"
            
            params = {'task_name':'文章内容概要'}
            
            d = requests.get(url, params=params).json()
            
            print(d)
            
            d['task_name'] = params.get('task_name')
            
            d['task_value'] = '...............'
            
            d = requests.post(url, data=d).json()
            
            print(d)
            # data = {
            #     "id": 1,
            #     "text": '测试。。。。。。。。。。。。',
            # }
            # r = requests.post(url, data=data).json()
            # print(r)
            return

        if options.get("爬取所有医生号的所有视频"):
            间隔秒数 = 3600 * 24
            while 1:
                需要抓取视频的账号列表 = 抖音医生号.获取需要爬取的账号(间隔秒数)
                if 需要抓取视频的账号列表:
                    kill_chrome()
                for obj in 需要抓取视频的账号列表:
                    obj.全部抓取所有视频()
                    obj.save()
                kill_chrome()
                获取字幕()
                time.sleep(1)
                # kill_chrome()

        if options.get("get_subtitle"):
            kill_chrome()
            获取字幕()
                
        if options.get("run"):
            运行所有任务()

        if options.get("step"):
            # kill_chrome()
            单步运行()
