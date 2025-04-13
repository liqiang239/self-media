import yaml
from .constants import API_RET_CODE_OK
from my_project.settings import BASE_DIR


def api_ret_data(data=None):
    return {'code': API_RET_CODE_OK, 'msg': 'ok', 'data': data or {}}


def get_file_suffix(fpath):
    return fpath.split('.')[-1]


def get_file_name(fpath):
    fpath = fpath.replace('\\', '/')
    return fpath.split('/')[-1]


# def load_configs():
#     with open(f'{BASE_DIR}/config/config.yml', 'r', encoding='utf-8') as f:
#         configs = yaml.load(f.read(), yaml.Loader)
#         return configs