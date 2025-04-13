import os
import shutil
import sys
import platform
from pathlib import Path
from subprocess import call


current_file = sys.argv[0]
BASE_DIR = Path(current_file).resolve().parent.parent
PACK_DIR = BASE_DIR / 'pack'

exec_file_name = ''
if platform.system() == 'Windows':
    exec_file_name = 'manage.exe'
elif platform.system() == 'Linux':
    exec_file_name = 'manage'

def run_cmd(cmd):
    ret = call(cmd, shell=True)
    if ret != 0:
        print(f'执行错误: {cmd}')
        raise


def run_manage(args_str):
    """执行manage.exe"""
    run_cmd(f'{PACK_DIR}/dist/manage/{exec_file_name} {args_str}')


def pack():
    """打包"""
    cmd = 'pyinstaller manage.spec -y --clean'
    run_cmd(cmd)


def init_db():
    """初始化数据库"""
    init_dir = f'{PACK_DIR}/dist/manage/db/sg'
    if not os.path.lexists(init_dir):
        os.makedirs(init_dir)
    run_manage('migrate')
    run_manage('migrate --database=base')


def init_jobs():
    """初始化任务"""
    run_manage('cmd --import_all')


def create_superuser():
    run_manage('createsuperuser')


def start_server():
    run_manage('runserver --noreload')


def run_jobs():
    run_manage('cmd --long_run')


def init_venv():
    """初始化venv"""
    run_cmd('python -m venv venv')


def install_requirements():
    run_cmd(f'pip install -r {BASE_DIR}/requirements.txt')
    run_cmd('pip install pyinstaller')


def remove_exsited_pack():
    build_dir = f'{PACK_DIR}/build'
    dist_dir = f'{PACK_DIR}/dist'
    if os.path.lexists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.lexists(dist_dir):
        shutil.rmtree(dist_dir)





def main(is_remove_existed=False):
    if is_remove_existed:
        remove_exsited_pack()
    pack()
    # init_db()
    # create_superuser()


if __name__ == '__main__':
    opt = sys.argv[1]
    if opt == 'init_venv':
        init_venv()
    elif opt == 'install':
        install_requirements()
    elif opt == 'pack':
        main(is_remove_existed=True)
    elif opt == 'runserver':
        start_server()
    elif opt == 'run_jobs':
        run_jobs()

    # init_run_job_bat()
    # install_req()
    # remove_exsited_pack()
