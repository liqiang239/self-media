from django.db import models

# Create your models here.
import datetime
import json
import os
import re
import time

from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Avg, Max, Min
from django.db.models.expressions import F
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.functional import cached_property
import pandas
import requests
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

from base.tool_comment_reply import 统计字数, 清理表情
from caidao_tools.django.abstract import AbstractModel
from helper_cmd import CmdProgress
from tool_dict import PropDict
from tool_gzip import gzip_compress, gzip_decompress
from tool_static import 存储链接到文件
from my_project.settings import CONFIGS
from helper_douyin import 抖音爬虫

from simple_comments.models import 评论, 回复


class 头条新闻(AbstractModel):
    ClusterId = models.BigIntegerField(null=True)
    Title = models.CharField(max_length=255, null=True)
    LabelUrl = models.URLField(null=True)
    Label = models.CharField(max_length=255, null=True)
    Url = models.URLField(null=True)
    HotValue = models.BigIntegerField(null=True)
    Schema = models.CharField(max_length=255, null=True)
    LabelUri = models.TextField(null=True)
    ClusterIdStr = models.CharField(max_length=255, null=True)
    ClusterType = models.SmallIntegerField(null=True)
    QueryWord = models.CharField(max_length=255, null=True)
    InterestCategory = models.TextField(null=True)
    Image = models.TextField(null=True)
    LabelDesc = models.CharField(max_length=255, null=True)
    所属榜单 = models.CharField(max_length=20, default='热榜')
    
    评论爬取次数 = models.IntegerField(default=0)
    快讯制作次数 = models.IntegerField(default=0)
    文章内容概要 = models.TextField(null=True)
    文章内容概要_完成 = models.BooleanField(default=False, db_index=True)

    ptn_url1 = re.compile("^https://www\.toutiao\.com/article/(\d+).*")
    ptn_url2 = re.compile("^https://www\.toutiao\.com/trending/(\d+).*")

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "ClusterId",
                ]
            ),
            models.Index(
                fields=[
                    '评论爬取次数',
                    "create_time",
                ]
            ),
            models.Index(
                fields=[
                    "update_time",
                ]
            ),
            # models.Index(fields=['status',]),
        ]

    # q = cls.objects.filter(create_time__lte=timezone.now() - datetime.timedelta(days=保质期天数))

    def __str__(self):
        return f"[{self.id}]{self.Title}"

    @classmethod
    @atomic(using="simple_news", savepoint=True)
    def 按时间自动生成快讯内容(cls, 所属榜单, 是否测试快讯=False):
        # 快讯制作记录 = cls.生成一条新快讯(
        #     cls.根据当前北京时间生成标题(所属榜单), 所属榜单, 是否测试快讯=是否测试快讯
        # )

        # 榜单条数字典 = 根据当前北京时间得到新闻榜条数()
        # 榜单条数字典 = {"默认主榜单": 10}
        s = time.time()
        # df = 处理记录.选择数据帧()
        result_total = 10
        df = 头条新闻.df(24)
        df["匹配榜单"] = df.所属榜单 == 所属榜单
        e = time.time()
        print("time0:", e - s)
        df = df.sort_values(by=["匹配榜单", "热议"], ascending=[False, False])
        df = df[df["快讯制作次数"] == 0]

        df_main = df.iloc[:result_total]
        # return df_main

        # if len(df_main[df_main.匹配榜单]) < result_total:
        #     error = f"应获取条数: {result_total}, 实际条数: {len(df_main[df_main.匹配榜单])}"

        #     快讯制作记录.备注["NotEnoughShortNewsError"] = error
        #     快讯制作记录.save()

        q = 头条新闻.objects.filter(id__in=df_main.id)
        s = time.time()
        分段数据 = list(
            map(
                lambda x: x.设置并得到拉取字典(
                    debug=是否测试快讯,
                    是否获取前排评论=False,
                ),
                q,
            )
        )
        e = time.time()
        print("time:", e - s)
        # 快讯制作记录.save()
        # return 快讯制作记录
        return 分段数据


    @property
    def 拉取字典(self):
        return {
            "id": self.id,
            "url": self.Url,
            "标题": self.Title,
            # "首图链接": self.首图链接,
            "前排评论回复文本": self.前排评论回复文本,
            "所属榜单": self.所属榜单
        }

    @property
    def 拉取简单字典(self):
        return {
            "id": self.id,
            "url": self.Url,
            "标题": self.Title,
            # "首图链接": self.首图链接,
            "所属榜单": self.所属榜单
        }

    def 设置并得到拉取字典(self, debug=False, 是否获取前排评论=True):
        if 是否获取前排评论:
            d = self.拉取字典
        else:
            d = self.拉取简单字典
        if not debug:
            self.快讯制作次数 += 1
            self.save()
        return d


    @property
    def 所有评论(self):
        return 评论.objects.filter(ClusterId=self.ClusterId)

    
    @classmethod
    def 得到最早需爬取评论的新闻(cls):
        return cls.objects.order_by('评论爬取次数','create_time').first()
    
    @property
    def 首图链接(self):
        return eval(self.Image).get("url")

    @classmethod
    def 删除所有n天前的新闻(cls, n=10):
        cls.objects.filter(
            create_time__lt=timezone.now() - datetime.timedelta(days=n)
        ).delete()

    @classmethod
    def 是否需要刷新(cls, 间隔分钟数=5):
        return (
            cls.objects.filter(
                create_time__gte=timezone.now()
                - datetime.timedelta(seconds=60 * 间隔分钟数),
                # 所属榜单='热榜'
            ).first()
            is None
        )

    # @classmethod
    # def 是否需要刷新分类热榜(cls, 间隔分钟数=60):
    #     return (
    #         cls.objects.filter(
    #             create_time__gte=timezone.now() - datetime.timedelta(seconds=60 * 间隔分钟数),
    #         ).exclude(所属榜单='热榜').first()
    #         is None
    #     )

    @classmethod
    def 得到n小时内新闻列表(cls, hours):
        return cls.objects.filter(
            create_time__gte=timezone.now() - datetime.timedelta(hours=hours)
        )

    @classmethod
    def df(cls, hours=24):
        q = cls.得到n小时内新闻列表(hours=hours)
        df = pandas.DataFrame(q.values("id", "ClusterId", "Title", "所属榜单","快讯制作次数"))
        df['热议'] =  df.ClusterId.apply(lambda x: 评论.objects.filter(ClusterId=x).count())
        return df

    def go(self, 爬虫):
        if not self.检验当前页面是否为当前新闻(爬虫):
            爬虫.go(self.Url)
        else:
            爬虫.driver.refresh()

    def 检验当前页面是否为当前新闻(self, 爬虫):
        url = 爬虫.driver.current_url
        for ptn in (self.ptn_url1, self.ptn_url2):
            m = ptn.match(url)
            if m is not None:
                return int(m.groups()[0]) == self.ClusterId
        return False

    @property
    def url_start(self):
        return self.Url.split("?", maxsplit=1)[0]

    def 得到页面内容(self, 爬虫):
        l = 爬虫.搜索请求(self.url_start)
        if l:
            return 爬虫.get_content(l[0][1])

    def 存储评论(self, 爬虫):
        新建计数 = 0
        for i, x in enumerate(爬虫.所有评论):
            print(i, x.get("id"))
            # x['新闻'] = self
            x["ClusterId"] = self.ClusterId
            _, created = 评论.objects.update_or_create(
                id=x.get("id"),
                defaults=x,
            )
            if created:
                print("\t", x.get("text"))
            新建计数 += created
        return 新建计数

    def 存储回复(self, 爬虫):
        for i, x in enumerate(爬虫.所有回复):
            print(i, x.get("id"), "=" * 10)
            _, created = 回复.objects.update_or_create(
                id=x.get("id"),
                defaults=x,
            )
            if created:
                print("\t", x.get("text"))

    def 爬取所有回复(self, 爬虫):
        cnt_ElementClickInterceptedException = 0
        cnt_StaleElementReferenceException = 0
        while 1:
            try:
                e = 爬虫.第一个查看全部回复
                if e is None:
                    break
                爬虫.移动到元素(e)
                time.sleep(0.1)
                e.click()
                # 爬虫.安全点击(e)
                time.sleep(1)
                爬虫.刷新日志()
                self.存储回复(爬虫)
                self.存储评论(爬虫)
            except StaleElementReferenceException as e:
                cnt_StaleElementReferenceException += 1
                print(cnt_StaleElementReferenceException, type(e), e)
                time.sleep(1)
            except ElementClickInterceptedException as e:
                print(cnt_ElementClickInterceptedException, type(e), e)
                cnt_ElementClickInterceptedException += 1
                if cnt_ElementClickInterceptedException >= 3:
                    break
                time.sleep(1)
                element = 爬虫.第一个查看全部回复
                if element is not None:
                    爬虫.移动到元素(element)
                    time.sleep(0.1)
                    爬虫.driver.execute_script(
                        "arguments[0].scrollIntoView();", element
                    )

    def 安全存储评论(self, 爬虫, 页面高度变化):
        for i in range(3):
            time.sleep(2)
            爬虫.刷新日志()
            没有新评论 = self.存储评论(爬虫) <= 0
            if not 没有新评论:
                return 没有新评论

            if 页面高度变化 >= 100:
                print("++++++++++++++++重新尝试获取加载的评论:...", i)
                continue
        return True

    def 爬取评论(self, 爬虫):
        self.go(爬虫)
        爬虫.刷新日志()
        # self.处理记录.存储页面(爬虫)
        self.存储评论(爬虫)
        self.爬取所有回复(爬虫)
        while 1:
            页面高度变化 = 爬虫.滚动至浏览器底部()
            time.sleep(1)
            爬虫.刷新日志()
            没有新评论 = self.存储评论(爬虫) <= 0
            # 没有新评论 = self.安全存储评论(爬虫, 页面高度变化)
            self.爬取所有回复(爬虫)
            if 没有新评论 and 页面高度变化 <= 0:
                break
        # self.处理记录.评论刷新次数加1()
        self.评论爬取次数 += 1
        self.save()

    # @property
    # def 处理记录(self):
    #     return 处理记录.objects.filter(ClusterId=self.ClusterId).first()

    #
    # @property
    # def 状态(self):
    #     return self.处理记录.status
    #
    # def 设置状态(self, 状态):
    #     处理记录 = self.处理记录
    #     处理记录.status = 状态
    #     处理记录.save()

    @classmethod
    def 第一个需要更新的记录(cls):
        return cls.objects.filter(status=None).first()

    @classmethod
    def 是否有非法字段(cls, d):
        for k in d.keys():
            if k not in cls.get_fields():
                print('k', k)
                return True

    @classmethod
    def 刷新热榜(cls, 爬虫):
        爬虫.go_homepage()
        time.sleep(5)
        爬虫.刷新日志()
        resp = 爬虫.得到第一个热榜请求内容()
        if resp:
            l = resp["data"]
            objs = []
            for d in l:
                if cls.是否有非法字段(d):
                    print(d)
                    raise ValueError
                objs.append(cls(**d))
            cls.objects.bulk_create(objs)
            return True


    @classmethod
    @atomic(using="simple_news", savepoint=True)
    def 刷新分类热榜数据(cls, resp):
        if resp:
            l = resp["data"]
            # objs = []
            for raw_content in l:
                content = json.loads(raw_content['content'])
                所属榜单 = content['raw_data']['board'][0]['hot_board_title']
                if 所属榜单 == '热榜':
                    continue
                hot_board_items = content['raw_data']['board'][0]['hot_board_items']
                for d in hot_board_items:
                    # print(d)
                    data = {
                        'ClusterId': d['id'],
                        'Title': d['title'],
                        'LabelUrl': d['title_label_image']['url'] if d['title_label_image'] else None,
                        'Label': d['title_label_type'],
                        'Url': f'https://www.toutiao.com/trending/{d["id"]}/',
                        'HotValue': 0,
                        'Schema': d['schema'],
                        'LabelUri': d['title_label_image'],
                        'ClusterIdStr': d['id_str'],
                        'ClusterType': d['log_pb']['cluster_type'],
                        'QueryWord': '',
                        'Image': '{}',
                        'LabelDesc': d['title_label_desc'],
                        '所属榜单': 所属榜单
                    }
                    if cls.是否有非法字段(data):
                        print(d)
                        raise ValueError
                    cls.objects.update_or_create(ClusterId=d['id'], defaults=data)
            return True



    @classmethod
    def 刷新分类热榜(cls, 爬虫):
        爬虫.打开分类榜单页面()
        time.sleep(5)
        爬虫.刷新日志()
        resp = 爬虫.得到第一个分类热榜请求内容()
        cls.刷新分类热榜数据(resp)
        return True
