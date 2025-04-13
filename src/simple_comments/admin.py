from django.contrib import admin
from caidao_tools.django.base_admin import BaseAdmin


from .models import 评论, 回复
# Register your models here.


@admin.register(评论)
class 评论Admin(BaseAdmin):
    pass

@admin.register(回复)
class 回复Admin(BaseAdmin):
    pass