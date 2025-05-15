from django.contrib import admin

# Register your models here.
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from caidao_tools.django.base_admin import BaseAdmin
from docshare.models import 抖音医生号,抖音视频

# Register your models here.

from django.contrib.admin import SimpleListFilter

class DefaultDateFilter(SimpleListFilter):
    title = '发布时间'
    parameter_name = 'publish_date'

    def lookups(self, request, model_admin):
        return (('recent', '最近一周'),)

    def queryset(self, request, queryset):
        if not self.value():  # 无筛选参数时应用默认条件
            return queryset.filter(id__gte=100)
        return queryset


@admin.register(抖音医生号)
class 抖音医生号Admin(BaseAdmin):
    pass


@admin.register(抖音视频)
class 抖音视频Admin(BaseAdmin):
    list_display = ("id", "视频字幕", '是否有用','是否用过', "抖音号", "唯一号", "视频标题or描述", "视频链接本地")
    list_filter = ('抖音号__抖音号', '是否有用', '是否用过')
    list_editable = ('是否有用','是否用过')  # 启用行内编辑

    ordering = ('id', )

    def is_valid(self, obj):
        return mark_safe(
            f'''
            <input type="checkbox" 
                   name="是否有用" 
                   {'checked' if obj.是否有用 else ''} 
                   class="htmx-checkbox">
            '''
        )
    is_valid.short_description = '勾选是否有用'

    def 视频标题or描述(self, obj):
        return obj.视频标题 or obj.视频描述[:100]

    def changelist_view(self, request, extra_context=None):
        # if not request.GET:
        #     # 设置默认筛选条件：仅显示 visible=True 且 hidden=False 的记录
        #     request.GET = request.GET.copy()
        #     request.GET["visible"] = "1"  # 假设 visible 是布尔字段，1 表示 True
        #     request.GET["hidden"] = "0"  # 0 表示 False
        #     request.GET._mutable = False
        # print(dir(request.GET))
        request.GET = request.GET.copy()
        request.GET.update({'是否淘汰': False})  # 假设 visible 是布尔字段，1 表示 True
        request.GET._mutable = False
        return super().changelist_view(request, extra_context)

