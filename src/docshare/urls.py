from django.urls import path

from .views import 基础任务制作接口

urlpatterns = [
    path('tasks', 基础任务制作接口.as_view()),
]