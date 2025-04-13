from rest_framework.views import APIView
from django.http.response import JsonResponse

from django.shortcuts import render

from caidao_tools.django.abstract_views import 抽象任务制作接口
from .models import 头条新闻
# Create your views here.


class 基础任务制作接口(抽象任务制作接口):
    def get(self, request):
        return super().get(request, 头条新闻)
    
    def post(self, request):
        return super().post(request, 头条新闻)
