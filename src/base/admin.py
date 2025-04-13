from django.contrib import admin

from base.models import 头条热榜新闻, 评论, 回复, 处理记录
from caidao_tools.django.base_admin import BaseAdmin
from django.utils.safestring import mark_safe


# Register your models here.


@admin.register(头条热榜新闻)
class 头条热榜新闻Admin(BaseAdmin):
    list_display_exclude = (
        "Url",
        "LabelUri",
        "LabelUrl",
        "Image",
        # 'update_time',
        "create_time",
        "Schema",
        "ClusterIdStr",
    )

    search_fields = [
        "ClusterId",
    ]


@admin.register(评论)
class 评论Admin(BaseAdmin):
    search_fields = ["text", "id"]

    list_display_exclude = (
        "content_rich_span",
        "id_str",
        "reply_list",
        "new_reply_list",
        "vote_info",
    )

    list_display_replace = {"ClusterId": "info_view", "reply_count": "回复数"}

    def info_view(self, obj):
        return mark_safe(
            f"""
        {obj.ClusterId} <br/>
        <a href="{obj.最新.Url if obj.最新 else ''}" target="_blank">{obj.最新.Title if obj.最新 else '-'}</a> <br/>
        评分:{obj.评分} <br/>
    """
        )

    def 回复数(self, obj):
        return mark_safe(
            f"""
        <a href="/admin/base/回复/?评_id={obj.id}" target="_blank">{obj.reply_count}</a>
    """
        )


@admin.register(回复)
class 回复Admin(BaseAdmin):
    search_fields = ["text", "id"]

    list_display_exclude = (
        "id_str",
        "create_time",
        "content_rich_span",
        "user",
        "digg_prompt",
        "star_comment_info",
    )

    list_display_replace = {
        "评": "info_view",
    }

    readonly_fields = ("评",)

    def info_view(self, obj):
        return mark_safe(
            f"""
        <a href="{obj.评.最新.Url if obj.评.最新 else ''}" target="_blank">{obj.评.最新.Title if obj.评.最新 else '-'}</a> <br/>
        <hr>
        {obj.评.text} <a target="_blank" href="/admin/base/%E5%9B%9E%E5%A4%8D/?评_id={obj.评.id}">[{obj.id}]</a><br/>
    """
        )


@admin.register(处理记录)
class 处理记录管理(BaseAdmin):
    list_display_exclude = ("html_bin",)

    list_display_replace = {
        "ClusterId": "info_view",
        "create_time": "类别",
    }

    list_filter = ("selected", "快讯制作次数")

    def info_view(self, obj):
        return mark_safe(
            f"""
        <a href="{obj.最新.Url if obj.最新 else ''}" target="_blank">{obj.最新.Title if obj.最新 else '-'}</a> <br/>
        <hr>
        <a href="/admin/base/评论/?ClusterId={obj.ClusterId}" target="_blank">{obj.ClusterId}</a>
    """
        )
