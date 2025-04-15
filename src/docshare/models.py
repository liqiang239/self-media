from django.db import models
from django.forms import model_to_dict

# Create your models here.

from caidao_tools.django.abstract import AbstractModel
from helper_douyin import 抖音爬虫
from django.db.transaction import atomic
import time
from selenium.webdriver.common.keys import Keys


class 抖音医生号(AbstractModel):
    抖音号 = models.CharField(max_length=50, unique=True)
    链接 = models.URLField(default='')
    已全部抓取 = models.BooleanField(default=False)

    def __str__(self):
        return self.抖音号

    def 爬虫到主页(self):
        pa = 抖音爬虫.得到爬虫单例()
        pa.go(self.链接)
        time.sleep(3)
        e = pa.find_element_css(
            "#user_detail_element > div > div.o1w0tvbC.F3jJ1P9_.InbPGkRv.W41XVmRl > div.mZmVWLzR > div.ds1zWG9C > h1 > span > span > span > span > span > span"
        )
        e.click()
        return pa

    @property
    def 当前页面数据字典(self):
        pa = 抖音爬虫.得到爬虫单例()
        return list(pa.得到所有json("https://www.douyin.com/aweme/v1/web/aweme/post"))

    @property
    def 当前页视频字典列表(self):
        rtn = []
        for d in self.当前页面数据字典:
            the_list = map(
                lambda x: 抖音视频.解析视频字典(x, self), d.get("aweme_list")
            )
            rtn.extend(list(the_list))
        return rtn

    def 爬取并存储当前页所有视频(self):
        return 抖音视频.解析并存储视频列表(self.当前页视频字典列表 or [])

    def 滚动到底部(self, pa):
        pa.page_down()
        time.sleep(3)
        pa.刷新日志()

    @property
    def 根字典(self):
        d = {}
        for x in self.当前页面数据字典:
            if x.get("has_more"):
                d["has_more"] = x.get("has_more")
        return d

    def 全部抓取所有视频(self):
        pa = self.爬虫到主页()
        retry_cnt_pagedown = 0
        max_retry_cnt_pagedown = 20
        total_cnt = 0
        i = 0
        while 1:
            total_cnt += self.爬取并存储当前页所有视频()

            if self.已全部抓取:
                break
            d = self.根字典
            print(
                "index:",
                i,
                "has more:",
                d.get("has_more"),
                "retry_cnt_pagedown:",
                retry_cnt_pagedown,
                "total_cnt:",
                total_cnt,
            )
            i += 1
            if d.get("has_more") == 1:
                print("page down....:", len(d))
                self.滚动到底部(pa)
                retry_cnt_pagedown = 0
            else:
                retry_cnt_pagedown += 1
                if retry_cnt_pagedown >= max_retry_cnt_pagedown:
                    break
                else:
                    print("page down....:", len(d))
                    self.滚动到底部(pa)
        if not self.已全部抓取:
            self.已全部抓取 = True
            self.save()


# https://v96.douyinvod.com/d199fd3b8cbd768a6dd8d6d31fc355ef/67ee43e3/video/tos/cn/tos-cn-ve-15/oAF3GQsIDXB6fCAqAEfVAngeFFJgyMBBbxa76w/?a=1128&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&cv=1&br=1391&bt=1391&cs=0&ds=4&ft=V4TLtMPfRR0s~dC52Dv2Nc0iPMgzbLZAS21U_4~fCjV9Nv7TGW&mime_type=video_mp4&qs=0&rc=ZGU0aGZnaGY7Njo4ZTo6ZUBpam9oZnI5cmV5czMzNGkzM0AzLi5fXjNiNWAxX19iYmM1YSMzMi5mMmQ0cWtgLS1kLTBzcw%3D%3D&btag=c0000e000a8000&cc=2c&cquery=100y&dy_q=1743664446&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&l=2025040315140678D421EAE4C9AF04340D&req_cdn_type=
class 抖音视频(AbstractModel):
    抖音号 = models.ForeignKey("抖音医生号", on_delete=models.CASCADE)
    唯一号 = models.PositiveBigIntegerField(null=True)
    视频链接 = models.URLField()
    视频字幕 = models.TextField()
    视频字幕_完成 = models.BooleanField(default=False, db_index=True)
    视频标题 = models.CharField(max_length=100)
    视频描述 = models.TextField(null=True)
    分享链接 = models.URLField(null=True)
    视频链接本地 = models.URLField(null=True)
    文案 = models.TextField(null=True)
    文案_完成 = models.BooleanField(default=False, db_index=True)
    是否淘汰 = models.BooleanField(default=False, db_index=True)
    是否用过 = models.BooleanField(default=False, db_index=True)

    @classmethod
    def 清理所有状态(cls):
        cls.objects.filter().update(视频字幕_完成=False, 文案_完成=False)

    # @classmethod
    # def 得到一条任务(cls, 字段名称):
    #     return cls.objects.filter(**{f'{字段名称}_完成':False}).order_by('create_time').first()

    # @classmethod
    # def 得到一条任务json(cls, 字段名称):
    #     obj = cls.得到一条任务(字段名称)
    #     return obj.json if obj is not None else {}

    # def 设置制作结果(self, name, value):
    #     setattr(self, f'{name}', value)
    #     setattr(self, f'{name}_完成', True)
    #     self.save()
    
    # def 设置字幕(self, text):
    #     self.视频字幕 = text
    #     self.视频字幕_完成 = True
    #     self.save()

    # def 设置文案(self, text):
    #     self.文案 = text
    #     self.文案_完成 = True
    #     self.save()

    # def __getattr__(self, name):
    #     name_prefix = name.rsplit("_")[0]
    #     if self.has_field(name_prefix) and self.has_field(f'{name}_完成') and name.endswith('_json'):
    #         return {'id':self.id, }
        
    # @property
    # def 视频字幕_json(self):
    #     pass
    
    # @property
    # def json(self):
    #     return model_to_dict(self)
        # return {"id":self.id,
        #         "唯一号": self.唯一号,
        #         "视频链接": self.视频链接,
        #         "视频标题": self.视频标题,
        #         "视频描述": self.视频描述,
        #         "分享链接": self.分享链接,
        #         "视频字幕": self.视频字幕,
        #         "视频字幕_完成": self.视频字幕_完成,
        #         "文案": self.文案,
        #         "文案_完成": self.文案_完成,
        #         "视频链接本地": self.视频链接,
        #         }
    
    
    @classmethod
    def 解析视频字典(cls, d, dyh):
        return {
            "视频链接": next(
                filter(
                    lambda x: x.startswith("https://www.douyin.com"),
                    d["video"]["play_addr"]["url_list"],
                )
            ),
            "视频标题": d["item_title"],
            # '视频字幕': d['share_info'],
            "视频描述": d["desc"],
            "分享链接": d["share_url"],
            "唯一号": d["aweme_id"],
            "抖音号": dyh,
        }

    @classmethod
    @atomic(using="docshare", savepoint=True)
    def 解析并存储视频列表(cls, lst):
        for d in lst:
            cls.objects.get_or_create(唯一号=d["唯一号"], defaults=d)
        return len(lst)


class 公众号文章(AbstractModel):
    公众号名称 = models.CharField(max_length=100)
    文章链接 = models.URLField()
    文章标题 = models.CharField(max_length=100)
    文章内容 = models.TextField()

    def __str__(self):
        return self.文章标题
