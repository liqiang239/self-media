from rest_framework.views import APIView
from django.http.response import JsonResponse

# from commons.exceptions import ShortNewsNotFoundError
# from kuaixun.models import 快讯制作
from simple_news.models import 头条新闻


# # Create your views here.
# class 新闻快讯双播音频接口(APIView):
#     def get(self, request):
#         data = 快讯制作.得到第一条未制作的快讯音频的任务字典()
#         return JsonResponse(data)

#     def post(self, request):
#         快讯制作id = request.POST.get("id")
#         音频链接 = request.POST.get("音频链接")
#         处理记录id = int(request.POST.get("处理记录id"))

#         obj = 快讯制作.objects.get(id=快讯制作id)
#         for d in obj.分段数据:
#             if d["id"] == 处理记录id:
#                 d["音频链接"] = 音频链接

#         if not obj.是否还有待制作分段音频():
#             obj.状态 = "待合并"
#         obj.save()

#         return JsonResponse({"data": {}, "messsage": "ok"})


class 新闻快讯双播音频接口_whole(APIView):
    def get(self, request):
        所属榜单 = request.GET.get("type")
        # 快讯制作记录ID = request.GET.get("id")
        是否测试快讯 = request.GET.get("是否测试快讯")
        是否测试快讯 = bool(是否测试快讯)

        分段数据 = 头条新闻.按时间自动生成快讯内容(所属榜单, 是否测试快讯)

        return JsonResponse(
            {
                "id": 1,
                "urls": [d["url"] for d in 分段数据],
            }
        )

        # 是否得到最后id = bool(request.GET.get("last"))
        # print('是否测试快讯', 是否测试快讯)
        # 是否测试快讯 = int(request.POST.get("debug", 0))
        # if 快讯制作记录ID:
        #     data = 快讯制作.得到第一条已制作的快讯音频记录字典(快讯制作记录ID)
        # elif 是否得到最后id:
        #     q = 快讯制作.objects.filter()
        #     if 所属榜单:
        #         q = q.filter(所属榜单=所属榜单)
        #     obj = q.last()
        #     # data = {
        #     #     "id": obj.id if obj else 0,
        #     # }
        #     data = obj.字典
        # else:
        #     data = 快讯制作.得到第一条未制作的快讯音频的任务字典_whole(所属榜单, 是否测试快讯=是否测试快讯)
        # return JsonResponse(data)

    # def post(self, request):
    #     快讯制作id = request.POST.get("id")
    #     音频链接 = request.POST.get("音频链接")
    #     所属榜单 = request.POST.get("type")
    #     备注 = json.loads(request.POST.get("remark", '{}'))

    #     try:
    #         obj = 快讯制作.更新快讯制作记录(快讯制作id, 所属榜单, 音频链接, 备注)
    #         ret_data = {"messsage": "ok", "id": obj.id}
    #     except ShortNewsNotFoundError as e:
    #         ret_data = {"message": e.msg}
    #     return JsonResponse(ret_data)


# class 新闻快讯双播音频下载(APIView):
#     def get(self, request):
#         category_name = request.GET.get("category_name")
#         obj = 快讯制作.得到当前时段快讯记录(category_name)
#         if not obj or not obj.音频链接:
#             return HttpResponse("当前时段音频还未生成", status=404)
#             # return JsonResponse({'data': {}, 'message': '当前时段音频还未生成'})
#         else:
#             # return HttpResponseRedirect(url)
#             file_path = 链接到路径(obj.音频链接)
#             file = open(file_path, "rb")
#             encoded_name = quote(f"{obj.标题}.{得到后缀(file_path)}")
#             response = FileResponse(file, content_type="audio/mpeg")
#             response["content_type"] = "application/octet-stream"
#             response["Content-Disposition"] = (
#                 f"attachment; filename*=UTF-8''{encoded_name}"
#             )
#             return response
