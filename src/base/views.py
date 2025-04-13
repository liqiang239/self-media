from django.shortcuts import render

from rest_framework.views import APIView

from django.http.response import JsonResponse

from apis.models import 任务表, 任务类型_头条新闻拉取,状态_等待中
from base.models import 处理记录

# class PullNewsAndComments(APIView):
#     def post(self, request):
#         obj = 任务表.得到10分钟之内的重复请求(任务类型_头条新闻拉取)
#         if obj is not None:
#             data_list = obj.任务数据
#         else:
#             data_list = 处理记录.拉取未制作快讯的前n条热议数据()
#             任务表.objects.create(
#                 任务类型=任务类型_头条新闻拉取,
#                 任务数据=data_list,
#                 状态=状态_等待中,
#             )
#         return JsonResponse({'data':data_list, 'messsage':'ok'})
