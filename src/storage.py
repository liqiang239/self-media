from django.core.files.storage import Storage

from commons.external_api import upload_file_by_bin
from commons.constants import FILE_SERVICE_HOST


class MyStorage(Storage):
    path = ""

    def __init__(self, path: str = ""):
        self.path = path
        if not path.endswith("/"):
            self.path = self.path + "/"

    def save(self, name, content, max_length=None):
        """
     文件保存
     :param name: 上传时的文件名称，包含后缀名
     :param content: 文件内容,File对象
     :param max_length: 文件最大二进制长度
     :return: 文件路径
     """
        # todo 处理保存文件逻辑，返回相对文件路径
        path = upload_file_by_bin(content.read())
        return path

    def delete(self, name):
        """
        删除文件
        :param name: 相对路径文件名，此处并非上传时的文件名，而是在save()函数中返回的文件名
        :return:
        """
        # todo 处理删除文件逻辑，无返回

    def url(self, name):
        """
        返回文件的url地址
        :param name: 相对路径文件名，此处并非上传时的文件名，而是在save()函数中返回的文件名
        :return:
        """
        # todo 处理返回文件url逻辑，返回文件的url地址
        furl = f'{FILE_SERVICE_HOST}{name}'
        # print('furl', furl)
        return furl

    def path(self, name):
        """
        返回文件的相对路径地址
        :param name: 相对路径文件名，此处并非上传时的文件名，而是在save()函数中返回的文件名
        :return: 相对路径地址
        """
        # todo 处理返回文件相对路径地址，一般返回name自身或者与url()一致，具体看自身业务逻辑
        return name

    def open(self, name, mode='rb'):
        """
        打开文件操作，一般pass即可
        :param name: 相对路径文件名，此处并非上传时的文件名，而是在save()函数中返回的文件名
        :param mode: 打开方式，默认'rb'
        :return:
        """
        pass
