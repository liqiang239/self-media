from io import BytesIO

import requests
from commons.constants import FILE_SERVICE_HOST, MAIL_SERVICE, MAIL_SERVICE_TOKEN
from commons.utils import get_file_name


def upload_file(fpath):
    url = f'{FILE_SERVICE_HOST}/api/file'
    fname = get_file_name(fpath)
    # mode = get_read_file_mode(fpath)
    form_data = {'file': (fname, open(fpath, 'rb'))}
    data = requests.post(url, files=form_data).json()
    print(data)
    return data['data']['url']


def upload_file_by_bin(bin_data):
    url = f'{FILE_SERVICE_HOST}/api/file'
    buf = BytesIO(bin_data)
    form_data = {'file': ('x.png', buf)}
    data = requests.post(url, files=form_data).json()
    print(data)
    return data['data']['url']


def send_email(title, content, to_list):
    url = f'{MAIL_SERVICE}/api/sendemail'
    headers = {'Token': MAIL_SERVICE_TOKEN}
    data = {"title": title, "content": content, "to_list": to_list}
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()

if __name__ == '__main__':
    upload_file('d:/tmp/test/3_save2.png')