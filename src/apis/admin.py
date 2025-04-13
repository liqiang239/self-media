from django.contrib import admin

from apis.models import 任务表
from caidao_tools.django.base_admin import BaseAdmin

# Register your models here.


@admin.register(任务表)
class 任务表Admin(BaseAdmin):
    list_filter = ('任务类型','状态')

    # def save_model(self, request, obj, form, change):
    #     print('lllllllllllllllllll')
    #     if not change:
    #         return
        
    #     print(form.changed_data)
    #     # if '任务数据' in form.changed_data:
    #     #     obj.confirmed = 1
    #     #     obj.save()


