import datetime
import functools
import os
import random
import subprocess
import sys
import time

import pytz


# echo = lambda info: os_system(f'echo "[$(date "+%m-%d-%H:%M:%S")] ({os.path.basename(sys._getframe().f_back.f_code.co_filename)}, line{sys._getframe().f_back.f_lineno})=> {info}"')
def echo(info, flush=True):
    print(f'{datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).strftime("[%m-%d %H:%M:%S]")} ({os.path.basename(sys._getframe().f_back.f_code.co_filename)}, line{sys._getframe().f_back.f_lineno})=> {info}', flush=flush)

os_system = functools.partial(subprocess.call, shell=True)
os_system_get_stdout = lambda cmd: subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
def os_system_get_stdout_stderr(cmd, wait=1):
    if wait <= 1:
        sp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')
    
    for i in range(wait):
        sp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sp.stdout.decode('utf-8'), sp.stderr.decode('utf-8')
        if len(out) > 0:
            return out, err
        print(f'[failed] `{cmd}`: {err.strip()}', file=sys.stderr, flush=True)
        time.sleep((1 + random.random()) * 2)
    return out, err


def time_str(fmt='[%m-%d %H:%M:%S]'):
    return datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime(fmt)


def unzip(zip_path):
    import os
    import os.path as osp
    import zipfile
    zip_out = osp.join(osp.dirname(zip_path), osp.basename(zip_path).split('.')[0])
    if os.path.exists(zip_out) and not osp.isdir(zip_out):
        zip_out += '_unzipped'
    os.makedirs(zip_out, exist_ok=True)
    fp = zipfile.ZipFile(zip_path, 'r')
    for x in fp.namelist():
        fp.extract(x, zip_out)
    fp.close()
