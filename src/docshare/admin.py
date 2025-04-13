from django.contrib import admin

# Register your models here.




from caidao_tools.django.base_admin import BaseAdmin
from docshare.models import 抖音医生号,抖音视频

# Register your models here.

@admin.register(抖音医生号)
class 抖音医生号Admin(BaseAdmin):
    pass


@admin.register(抖音视频)
class 抖音视频Admin(BaseAdmin):
    list_display = ("id", "视频字幕", "抖音号", "唯一号", "视频标题or描述", "视频链接本地")
    list_filter = ('抖音号', '视频字幕_完成', )

    def 视频标题or描述(self, obj):
        return obj.视频标题 or obj.视频描述[:100]

