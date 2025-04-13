class MsgException(Exception):
    default_msg = '{}'

    def __init__(self, msg=''):
        self.msg = self.default_msg.format(msg)


class MsgCodeException(MsgException):
    code = 4000

    def __init__(self, msg, code=None):
        super(MsgCodeException, self).__init__(msg=msg)
        self.code = code or self.code


class ParamsError(MsgCodeException):
    code = 4001

    default_msg = '参数错误:{}'


class UserNotFoundError(MsgCodeException):
    code = 4002

    default_msg = '未找到用户:{}'


class RecordExistedError(MsgCodeException):
    code = 4003

    default_msg = '已存在相同的数据, 创建失败:{}'


class RecordNotExistedError(MsgCodeException):
    code = 4004

    default_msg = '数据记录不存在:{}'


class NotEnoughShortNewsError(MsgCodeException):
    code = 4005
    default_msg = '快讯条数不够:{}'


class ShortNewsNotFoundError(MsgException):
    code = 4006
    default_msg = '未找到快讯制作记录:{}'