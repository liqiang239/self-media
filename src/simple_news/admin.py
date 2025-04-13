from django.contrib import admin
from caidao_tools.django.base_admin import BaseAdmin
from django.utils.safestring import mark_safe

from .models import 头条新闻
# Register your models here.


@admin.register(头条新闻)
class 头条新闻Admin(BaseAdmin):
    pass
