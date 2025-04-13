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


# Create your models here.

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
