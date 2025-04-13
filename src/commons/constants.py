import os

API_RET_CODE_OK = 2000
API_RET_CODE_PARAM_ERROR = 4000

FILE_SERVICE_HOST = os.getenv('FILE_SERVICE_HOST', 'https://file.j1.sale')

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
MAIL_SERVICE = os.getenv('MAIL_SERVICE', 'https://mail.j1.sale')
MAIL_SERVICE_TOKEN = os.getenv('MAIL_SERVICE_TOKEN', '2bcde9de3ccb4d5ac9623530011130c4')
