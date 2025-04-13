from rest_framework.views import APIView

from .exceptions import ParamsError
from django.http.request import QueryDict


class MyAPIView(APIView):

    @classmethod
    def check_serializer(cls, data, serializer):
        """序列化器检查"""
        s = serializer(data=data)
        if not s.is_valid():
            raise ParamsError(f'({",".join(s.errors.keys())})')
        return data

    def get_params_data(self, request):
        return request.GET

    def get_post_data(self, request, serializer=None):
        """尝试从表单和body中获取数据"""
        # 获取post请求数据
        data = request.data
        if isinstance(data, QueryDict):  # request.POST
            data = data.dict()

        # if serializer:
        #     self.check_serializer(data, serializer)
        return data

    def get_request_data(self, request):
        return self.get_params_data(request) or self.get_post_data(request)

    @classmethod
    def load_exception_data(cls, e, ret_data):
        """异常更新"""
        ret_data['msg'] = e.msg
        ret_data['code'] = e.code
        return ret_data
