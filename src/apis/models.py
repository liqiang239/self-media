from django.db import models
import datetime

from django.utils import timezone
from base.models import 处理记录
from django.db.models.expressions import F

# Create your models here.

任务类型_头条新闻拉取 = 0
任务类型_新闻抖音视频下载 = 1
任务类型_快讯音频制作 = 2

任务类型_choices = (
    (任务类型_头条新闻拉取, "头条新闻拉取"),
    (任务类型_新闻抖音视频下载, "新闻抖音视频下载"),
    (任务类型_快讯音频制作, "任务类型_快讯音频制作"),
)


状态_等待中 = 0
状态_执行中 = 1
状态_完成 = 2
状态_失败 = 3

状态_choices = (
    (状态_等待中, "等待中"),
    (状态_执行中, "执行中"),
    (状态_完成, "完成"),
    (状态_失败, "失败"),
)


class 任务表(models.Model):
    父任务 = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    任务类型 = models.IntegerField(
        default=任务类型_头条新闻拉取, choices=任务类型_choices
    )
    任务数据 = models.JSONField()
    状态 = models.IntegerField(default=状态_等待中, choices=状态_choices)
    创建时间 = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    更新时间 = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "任务类型",
                    "状态",
                    "创建时间",
                ],
            ),
            models.Index(
                fields=[
                    "父任务",
                ]
            ),
        ]

    @classmethod
    def 创建新闻快讯双播音频制作任务(cls, obj):
        data = {
            "id": obj.id,
        }
        return cls.objects.create(
            任务类型=任务类型_快讯音频制作,
            任务数据=data,
            状态=状态_执行中,
        )

    @classmethod
    def 创建新闻相关视频下载任务(cls, 处理记录id, urls: list[str]):
        for i, url in enumerate(urls):
            data = {
                "id": 处理记录id,
                "index": i,
                "url": url,
            }
            cls.objects.create(
                # 父任务_id=处理记录id,
                任务类型=任务类型_新闻抖音视频下载,
                任务数据=data,
            )

    @classmethod
    def 处理第一条任务(cls):
        task = cls.objects.filter(状态=状态_等待中).first()
        if task is not None:
            task.执行()
        return task

    @classmethod
    def 安全处理第一条任务(cls):
        try:
            return cls.处理第一条任务()
        except Exception as e:
            print("Exception:", e)

    @classmethod
    def 处理所有任务(cls):
        while cls.处理第一条任务() is not None:
            continue

    @property
    def 新闻处理记录(self):
        return 处理记录.objects.filter(id=self.任务数据.get("id")).first()

    @property
    def 抖音视频原始链接(self):
        return self.任务数据.get("url")

    def 是否抖音视频已经下载完成(self):
        return bool(self.新闻处理记录.抖音视频数据.get(self.抖音视频原始链接))

    def 下载抖音视频(self):
        from helper_douyin import 抖音爬虫

        url = 抖音爬虫.从头条爬虫单例拷贝实例().下载抖音视频(self.抖音视频原始链接)
        if url is not None:
            r = self.新闻处理记录
            r.抖音视频数据[self.抖音视频原始链接] = url
            r.save()
            self.状态 = 状态_完成
            self.save()

    def 执行(self):
        if self.任务类型 == 任务类型_头条新闻拉取:
            ids = [x.get("id") for x in self.任务数据]
            处理记录.objects.filter(id__in=ids).update(
                快讯制作次数=F("快讯制作次数") + 1
            )
            self.状态 = 状态_完成
            self.save()

        elif self.任务类型 == 任务类型_新闻抖音视频下载:
            if self.是否抖音视频已经下载完成():
                self.状态 = 状态_完成
                self.save()
            else:
                self.下载抖音视频()
        else:
            raise ValueError("未知的任务类型")

    @classmethod
    def 得到10分钟之内的重复请求(cls, 任务类型: int):
        return cls.objects.filter(
            任务类型=任务类型,
            状态__in=[状态_等待中, 状态_执行中],
            创建时间__gte=timezone.now() - datetime.timedelta(minutes=10),
        ).last()

    def 回写制作次数(self):
        pass
