from rest_framework.views import APIView
from django.http.response import JsonResponse

from django.shortcuts import render

from caidao_tools.django.abstract_views import 抽象任务制作接口
from .models import 抖音视频
# Create your views here.


class 基础任务制作接口(抽象任务制作接口):
    def get(self, request):
        return super().get(request, 抖音视频)
    
    def post(self, request):
        return super().post(request, 抖音视频)
