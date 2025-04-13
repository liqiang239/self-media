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

评论回复采集数量 = 40


def upload_file(content, fname, project_name="v5"):
    url = f"https://file.j1.sale/api/file"
    form_data = {"file": (fname, content)}
    data = {"project": project_name}
    data = requests.post(url, data=data, files=form_data).json()
    return "https://file.j1.sale" + data["data"]["url"]


# def 获取榜单处理顺序(榜单名称):
#     if 榜单名称 == '健康榜':
#         return 0
#     else:
#         return 1

class 头条热榜新闻(AbstractModel):
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
    # html_bin = models.BinaryField(null=True)
    # comments_bin = models.BinaryField(null=True)
    # status = models.CharField(max_length=20, null=True)

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
                所属榜单='热榜'
            ).first()
            is None
        )

    @classmethod
    def 是否需要刷新分类热榜(cls, 间隔分钟数=60):
        return (
            cls.objects.filter(
                create_time__gte=timezone.now() - datetime.timedelta(seconds=60 * 间隔分钟数),
            ).exclude(所属榜单='热榜').first()
            is None
        )

    @classmethod
    def 得到n小时内新闻列表(cls, hours):
        return cls.objects.filter(
            create_time__gte=timezone.now() - datetime.timedelta(hours=hours)
        )

    @classmethod
    def df(cls, hours=24):
        q = cls.得到n小时内新闻列表(hours=hours)
        return pandas.DataFrame(q.values("id", "ClusterId", "Title", "所属榜单"))

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
        self.处理记录.存储页面(爬虫)
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
        self.处理记录.评论刷新次数加1()

    @property
    def 处理记录(self):
        return 处理记录.objects.filter(ClusterId=self.ClusterId).first()

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
    def 保存分类热榜数据(cls, resp):
        if resp:
            l = resp["data"]
            objs = []
            for raw_content in l:
                content = json.loads(raw_content['content'])
                所属榜单 = content['raw_data']['board'][0]['hot_board_title']
                if 所属榜单 == '热榜':
                    continue
                hot_board_items = content['raw_data']['board'][0]['hot_board_items']
                for d in hot_board_items:
                    print(d)
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
                    # objs.append(d)
                    objs.append(cls(**data))
            # print(objs)
            cls.objects.bulk_create(objs)
            return True



    @classmethod
    def 刷新分类热榜(cls, 爬虫):
        爬虫.打开分类榜单页面()
        time.sleep(5)
        爬虫.刷新日志()
        resp = 爬虫.得到第一个分类热榜请求内容()
        cls.保存分类热榜数据(resp)
        return True
        # if resp:
        #     l = resp["data"]
        #     objs = []
        #     for raw_content in l:
        #         content = json.loads(raw_content['content'])
        #         所属榜单 = content['raw_data']['board'][0]['hot_board_title']
        #         hot_board_items = content['raw_data']['board'][0]['hot_board_items']
        #         for d in hot_board_items:
        #             data = cls.解析分类热榜数据(d)
        #             data['所属标签'] = 所属榜单
        #             objs.append(d)
        #             # objs.append(cls(**d))
        #     print(objs)
        #     # cls.objects.bulk_create(objs)
        #     return True


class 处理记录(AbstractModel):
    状态_新建 = 0
    状态_已创建抖音视频下载任务 = 1
    状态_已下载抖音视频 = 2
    状态_下载错误 = 3
    状态_choices = (
        (状态_新建, "新建"),
        (状态_已下载抖音视频, "已创建抖音视频下载任务"),
        (状态_已下载抖音视频, "已下载抖音视频"),
        (状态_下载错误, "下载错误"),
    )
    ClusterId = models.BigIntegerField(null=True, verbose_name="头条热榜新闻ClusterId")
    html_bin = models.BinaryField(null=True)
    selected = models.BooleanField(default=0)
    评论刷新次数 = models.PositiveSmallIntegerField(default=0)
    快讯制作次数 = models.PositiveSmallIntegerField(default=0)
    专题制作次数 = models.PositiveSmallIntegerField(default=0)
    详情输入链接 = models.URLField(null=True)
    首图本地链接 = models.URLField(null=True)
    # 下载的视频链接列表 = models.JSONField(null=True)
    状态 = models.PositiveSmallIntegerField(choices=状态_choices, default=状态_新建)
    抖音视频数据 = models.JSONField(null=True)
    双播快讯音频链接 = models.URLField(null=True)
    所有视频切分片段 = models.JSONField(null=True)
    
    快讯记录id = models.BigIntegerField(null=True)
    # 榜单处理顺序 = models.SmallIntegerField(default=0)
    所属榜单 = models.CharField(max_length=20, default='')

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "ClusterId",
                ]
            ),
            models.Index(
                fields=[
                    "selected",
                ]
            ),
            models.Index(
                fields=[
                    "状态",
                ]
            ),
            models.Index(
                fields=[
                    "双播快讯音频链接",
                ]
            ),

        ]


    # @classmethod
    # def 爬取一次(cls):
    #     if 头条热榜新闻.是否需要刷新(间隔分钟数=5):
    #         if 头条热榜新闻.刷新热榜(头条爬虫.得到爬虫单例()):
    #             处理记录.刷新n小时记录(8)
    #         else:
    #             print("刷新热榜失败")
    #             kill_chrome()
    #             return
    #         return


    #     t = 处理记录.得到第一个需要处理的记录()
    #     if t is not None:
    #         print(t, "开始爬取评论。。。")
    #         t.最新.爬取评论(头条爬虫.得到爬虫单例())

    @classmethod
    def 得到第一个需要制作快讯双播音频的记录(cls):
        obj = cls.objects.filter(双播快讯音频链接=None).first()
        obj.双播快讯音频链接 = ''
        obj.save()
        return obj

    def __str__(self):
        return f"处理记录[{self.id}] {self.最新}"

    def 是否全部下载完成(self):
        return all([v != "" for v in self.抖音视频数据.values()])

    def 回写下载记录(self, url, video_url):
        self.抖音视频数据[url] = video_url
        if self.是否全部下载完成():
            self.状态 = self.状态_已下载抖音视频
        self.save()

    def 创建抖音视频下载任务(self, 爬虫):
        from apis.models import 任务表

        爬虫 = 抖音爬虫.copy_driver(爬虫)
        data_list = 爬虫.搜索相关视频链接(self.最新.Title)
        任务表.创建新闻相关视频下载任务(self.id, data_list)
        self.状态 = self.状态_已创建抖音视频下载任务
        self.抖音视频数据 = {url: "" for url in data_list}
        self.save()

    @property
    def 类别(self):
        return
        # from damoxing.models import 新闻训练数据

        # obj = 新闻训练数据.objects.filter(ClusterId=self.ClusterId).first()
        # return obj.分类名 if obj is not None else None

    @property
    def 首图链接(self):
        if not self.最新.首图链接:
            return ''

        if not self.首图本地链接:
            self.首图本地链接 = 存储链接到文件(
                self.最新.首图链接, "jpeg", base_dir=CONFIGS.get("base_dir_56t")
            )
            self.save()
        return self.首图本地链接

    def 存储首图(self):
        # assert self.首图链接
        return self

    @classmethod
    def 选择数据帧(cls):
        l = list(cls.objects.filter(selected=1))
        cp = CmdProgress(len(l))
        data = []
        for x in l:
            data.append(x.选择字典)
            cp.update()
        return pandas.DataFrame(data=data)

    @property
    def 拉取字典(self):
        return {
            "id": self.id,
            "url": self.最新.Url,
            "标题": self.最新.Title,
            "首图链接": self.首图链接,
            "前排评论回复文本": self.前排评论回复文本,
            "所属榜单": self.所属榜单
        }

    @property
    def 拉取简单字典(self):
        return {
            "id": self.id,
            "url": self.最新.Url,
            "标题": self.最新.Title,
            "首图链接": self.首图链接,
            "所属榜单": self.所属榜单
        }

    def 设置并得到拉取字典(self, 快讯制作记录, debug=False, 是否获取前排评论=True):
        if 是否获取前排评论:
            d = self.拉取字典
        else:
            d = self.拉取简单字典
        # print('debug', debug)
        if not debug:
            # print('111111111111111111111111111111111')
            self.快讯记录id = 快讯制作记录.id
            self.快讯制作次数 += 1
            self.save()
        return d


    # @classmethod
    # def 为前n条热议新闻创建快讯制作记录(cls, n=10):
    #     from kuaixun.models import 快讯制作
    #     快讯制作记录 = 快讯制作.按时间自动生成快讯()
    #     df = cls.选择数据帧()
    #     df = df.sort_values(by=["热议"], ascending=False)
    #     df = df[df["快讯制作次数"] == 0].iloc[:n]
    #     ids = df.id
    #     q = cls.objects.filter(id__in=ids)
    #     快讯制作记录.分段数据 = list(map(lambda x: x.设置并得到拉取字典(快讯制作记录), q))
    #     快讯制作记录.save()
    #     return 快讯制作记录

    @property
    def 选择字典(self):
        return {
            "id": self.id,
            "热度": self.最新.HotValue,
            "热议": self.所有评论.count(),
            "热速": self.热速,
            "持久": self.持久,
            "快讯制作次数": self.快讯制作次数,
            "专题制作次数": self.专题制作次数,
            "所属榜单": self.所属榜单
        }

    @property
    def url(self):
        return self.最新.Url

    @property
    def 所有评论(self):
        return 评论.objects.filter(ClusterId=self.ClusterId)

    @property
    def 前排评论(self):
        l = filter(lambda x: x.字数, self.所有评论)
        l = sorted(list(l), key=lambda x: x.评分, reverse=True)
        return l[:评论回复采集数量]

    @property
    def 前排评论回复文本(self):
        return "\n\n".join(
            map(lambda x: f"【{x[0]}】 {x[1].文本}", enumerate(self.前排评论))
        )

    def 存储前排评论回复文本(self, fpath="d:/tmp"):
        fpath = os.path.join(fpath, f"{self.id}.txt")
        with open(fpath, "wb") as fp:
            fp.write(self.前排评论回复文本.encode("utf8"))
        return fpath

    @property
    def dict(self):
        return {
            "url": self.url,
            "comments": self.前排评论回复文本,
        }

    def 上传输入(self):
        content = json.dumps(self.dict).encode("utf8")
        self.详情输入链接 = upload_file(content, f"{self.id}.json")
        self.save()

    def 存储页面(self, 爬虫):
        self.html_bin = gzip_compress(爬虫.driver.page_source.encode("utf8"))
        self.save()

    def show_html(self):
        import webbrowser

        fpath = "d:/tmp/test.html"
        with open(fpath, "wb") as fp:
            fp.write(self.html.encode("utf8"))
        webbrowser.open(fpath)

    @property
    def html(self):
        return gzip_decompress(self.html_bin).decode("utf8")

    def 评论刷新次数加1(self):
        self.评论刷新次数 += 1
        self.save()

    def 快讯制作次数加1(self):
        self.快讯制作次数 += 1
        self.save()

    def 专题制作次数加1(self):
        self.专题制作次数 += 1
        self.save()

    @classmethod
    def 得到第一个需要下载抖音视频的记录(cls):
        q = cls.objects.filter(状态=cls.状态_新建)
        return q.first()
    

    @classmethod
    def 得到第一个需要处理的记录(cls):
        q = cls.objects.filter(selected=1)
        annotated_qs = q.annotate(
            fc=F("评论刷新次数")
        )
        min_fc = annotated_qs.aggregate(min_fc=Min("fc"))["min_fc"]
        if min_fc is not None:
            obj = annotated_qs.filter(fc__lte=min_fc).first()
            if obj.最新.首图链接:
                obj.存储首图()
            return obj

    @classmethod
    def 得到第一个需要处理的记录_老版本(cls):
        q = cls.objects.filter(selected=1)
        annotated_qs = q.annotate(
            fc=F("评论刷新次数") + F("快讯制作次数") + F("专题制作次数")
        )
        min_fc = annotated_qs.aggregate(min_fc=Min("fc"))["min_fc"]
        if min_fc is not None:
            obj = annotated_qs.filter(fc__lte=min_fc).first()
            if obj.首图本地链接:
                obj.存储首图()
            return obj

    @property
    def 所有(self):
        return 头条热榜新闻.objects.filter(ClusterId=self.ClusterId)

    @property
    def 最新(self):
        return self.所有.last()

    @property
    def 八小时内(self):
        return self.所有.filter(
            create_time__gte=timezone.now() - datetime.timedelta(seconds=60 * 60 * 8)
        )

    @property
    def 热速(self):
        q = self.八小时内.aggregate(
            max_value=Max("HotValue"), min_value=Min("HotValue")
        )
        return ((q.get("max_value") or 0) - (q.get("min_value") or 0)) / (60 * 60 * 8)

    @property
    def 持久(self):
        q = self.所有.aggregate(
            max_value=Max("create_time"), min_value=Min("create_time")
        )
        return (q.get("max_value") - q.get("min_value")).total_seconds() / 3600

    @classmethod
    @atomic(using="base", savepoint=True)
    def 刷新n小时记录(cls, hours=24):
        cls.objects.filter(selected=1).update(selected=0)
        df = 头条热榜新闻.df(hours)
        # for i in df.groupby(by="ClusterId").id.first().index:
        #     cls.objects.update_or_create(ClusterId=i, defaults={"selected": 1})

        for x in df.groupby(by="ClusterId"):
            cluster_id = x[0]
            # 所属榜单 = x[1]['所属榜单'].iloc[0]
            tmp = x[1]
            if tmp[tmp.所属榜单 !="热榜"].empty:
                所属榜单 = '热榜'
            else:
                所属榜单 = tmp[tmp.所属榜单 !="热榜"].所属榜单.iloc[0]
            # 所属榜单 = x[1]['所属榜单'].iloc[0]
            # 榜单处理顺序 = 头条热榜新闻.获取榜单处理顺序(所属榜单)
            cls.objects.update_or_create(ClusterId=cluster_id, defaults={"selected": 1, "所属榜单": 所属榜单})


class 评论(models.Model):
    id = models.BigIntegerField(primary_key=True)
    # 新闻 = models.ForeignKey(头条热榜新闻, null=True, on_delete=models.DO_NOTHING, db_constraint=False)
    ClusterId = models.BigIntegerField(null=True)
    id_str = models.CharField(max_length=255, null=True)
    text = models.CharField(max_length=255, null=True)
    content_rich_span = models.CharField(max_length=255, null=True)
    reply_count = models.SmallIntegerField(null=True)
    reply_list = models.TextField(null=True)
    new_reply_list = models.TextField(null=True)
    vote_info = models.TextField(null=True)
    digg_count = models.SmallIntegerField(null=True)
    bury_count = models.SmallIntegerField(null=True)
    forward_count = models.SmallIntegerField(null=True)
    create_time = models.IntegerField(null=True)
    score = models.FloatField(null=True)
    couplet_sticker = models.TextField(null=True)
    publish_loc_info = models.CharField(max_length=255, null=True)
    comment_tag_url = models.CharField(max_length=255, null=True)
    resource_url = models.CharField(max_length=255, null=True)
    user_id = models.BigIntegerField(null=True)
    user_name = models.CharField(max_length=255, null=True)
    remark_name = models.CharField(max_length=255, null=True)
    user_profile_image_url = models.URLField(null=True)
    user_verified = models.SmallIntegerField(null=True)
    interact_style = models.SmallIntegerField(null=True)
    is_following = models.SmallIntegerField(null=True)
    is_followed = models.SmallIntegerField(null=True)
    is_blocking = models.SmallIntegerField(null=True)
    is_blocked = models.SmallIntegerField(null=True)
    is_loyal_fan = models.SmallIntegerField(null=True)
    is_pgc_author = models.SmallIntegerField(null=True)
    author_badge = models.TextField(null=True)
    author_badge_night = models.TextField(null=True)
    verified_reason = models.CharField(max_length=255, null=True)
    user_bury = models.SmallIntegerField(null=True)
    user_digg = models.SmallIntegerField(null=True)
    user_relation = models.SmallIntegerField(null=True)
    user_auth_info = models.CharField(max_length=255, null=True)
    user_decoration = models.CharField(max_length=255, null=True)
    band_url = models.CharField(max_length=255, null=True)
    band_name = models.CharField(max_length=255, null=True)
    aid = models.SmallIntegerField(null=True)
    author_act_badge = models.TextField(null=True)
    auth_verified_info = models.CharField(max_length=255, null=True)
    comment_badge = models.TextField(null=True)
    comment_badge_night = models.TextField(null=True)
    large_image_list = models.TextField(null=True)
    thumb_image_list = models.TextField(null=True)
    media_info = models.TextField(null=True)
    tags = models.TextField(null=True)
    xg_badge_type = models.SmallIntegerField(null=True)
    platform = models.CharField(max_length=255, null=True)
    has_author_digg = models.SmallIntegerField(null=True)
    user_super_digg = models.SmallIntegerField(null=True)
    is_first_comment = models.SmallIntegerField(null=True)
    multi_media = models.TextField(null=True)
    has_multi_media = models.SmallIntegerField(null=True)
    show_tags = models.SmallIntegerField(null=True)
    is_repost = models.SmallIntegerField(null=True)
    dislike_style = models.SmallIntegerField(null=True)
    pendants = models.TextField(null=True)
    source = models.TextField(null=True)
    digg_bury_style = models.SmallIntegerField(null=True)
    membership_status = models.SmallIntegerField(null=True)
    support_react_list = models.TextField(null=True)
    reaction_info = models.TextField(null=True)
    star_comment_info = models.TextField(null=True)
    digg_prompt = models.TextField(null=True)
    extra = models.TextField(null=True)
    reply_to_comment = models.TextField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["ClusterId", "reply_count"]),
            models.Index(
                fields=[
                    "create_time",
                ]
            ),
        ]

    def __str__(self):
        return f"""评论网友:{self.user_name} {self.时间} 点赞：{self.digg_count}
    {清理表情(self.text)}"""

    @classmethod
    def 删除所有n天前的评论(cls, n=10):
        ts = (datetime.datetime.now() - datetime.timedelta(days=n)).timestamp()
        cls.objects.filter(create_time__lt=int(ts)).delete()

    @property
    def 前排回复(self):
        l = filter(lambda x: x.字数, self.回复_set.all())
        l = sorted(list(l), key=lambda x: x.评分, reverse=True)
        return l[:评论回复采集数量]

    @property
    def 字数(self):
        return 统计字数(self.text)

    @property
    def 评分(self):
        字数 = 统计字数(self.text)
        return (self.digg_count + 字数 * 0.001 + self.reply_count * 0.01) * (字数 != 0)

    @property
    def 文本(self):
        所有回复 = "\n".join(map(lambda x: str(x), self.前排回复))
        return "\n".join((str(self), 所有回复)).strip()

    @property
    def 时间(self):
        return datetime.datetime.fromtimestamp(self.create_time).strftime("%H:%M:%S")

    @cached_property
    def 最新(self):
        return 头条热榜新闻.objects.filter(ClusterId=self.ClusterId).last()

    @classmethod
    def 临时更新(cls):
        q = cls.objects.filter()
        cp = CmdProgress(q.count())
        for x in q:
            x.ClusterId = x.新闻.ClusterId
            x.save()
            cp.update()


class 回复(models.Model):
    id = models.BigIntegerField(primary_key=True)
    评 = models.ForeignKey(
        评论, null=True, on_delete=models.DO_NOTHING, db_constraint=False
    )
    id_str = models.CharField(max_length=255, null=True)
    create_time = models.IntegerField(null=True)
    text = models.CharField(max_length=255, null=True)
    content = models.CharField(max_length=255, null=True)
    content_rich_span = models.CharField(max_length=255, null=True)
    digg_count = models.SmallIntegerField(null=True)
    forward_count = models.SmallIntegerField(null=True)
    bury_count = models.SmallIntegerField(null=True)
    user_digg = models.SmallIntegerField(null=True)
    user_bury = models.SmallIntegerField(null=True)
    is_owner = models.SmallIntegerField(null=True)
    has_author_digg = models.SmallIntegerField(null=True)
    user_super_digg = models.SmallIntegerField(null=True)
    thumb_image_list = models.TextField(null=True)
    large_image_list = models.TextField(null=True)
    multi_media = models.TextField(null=True)
    has_multi_media = models.SmallIntegerField(null=True)
    publish_loc_info = models.CharField(max_length=255, null=True)
    user = models.TextField(null=True)
    group = models.TextField(null=True)
    repost_params = models.TextField(null=True)
    dislike_style = models.SmallIntegerField(null=True)
    digg_bury_style = models.SmallIntegerField(null=True)
    support_react_list = models.TextField(null=True)
    reaction_info = models.TextField(null=True)
    reply_badge = models.TextField(null=True)
    reply_badge_night = models.TextField(null=True)
    reply_to_comment = models.TextField(null=True)
    star_comment_info = models.TextField(null=True)
    digg_prompt = models.TextField(null=True)

    class Meta:
        indexes = [
            # models.Index(fields=['日期',]),
            models.Index(
                fields=[
                    "create_time",
                ]
            ),
        ]

    def __str__(self):
        return f"""
        回复网友:{self.用户数据.name} {self.时间} 点赞：{self.digg_count}
            {清理表情(self.content)}"""

    @classmethod
    def 删除所有n天前的回复(cls, n=10):
        ts = (datetime.datetime.now() - datetime.timedelta(days=n)).timestamp()
        cls.objects.filter(create_time__lt=int(ts)).delete()

    @property
    def 字数(self):
        return 统计字数(self.content)

    @property
    def 评分(self):
        字数 = self.字数
        return (self.digg_count + 字数 * 0.001 + self.forward_count * 0.01) * (
            字数 != 0
        )

    @property
    def 时间(self):
        return datetime.datetime.fromtimestamp(self.create_time).strftime("%H:%M:%S")

    @property
    def 用户数据(self):
        return PropDict(eval(self.user)) if self.user.startswith("{") else None
