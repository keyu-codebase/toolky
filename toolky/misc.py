import datetime
import functools
import os
import random
import subprocess
import sys
import time
from typing import Iterator

import pytz


# echo = lambda info: os_system(f'echo "[$(date "+%m-%d-%H:%M:%S")] ({os.path.basename(sys._getframe().f_back.f_code.co_filename)}, line{sys._getframe().f_back.f_lineno})=> {info}"')
def echo(info, flush=True):
    print(f'{datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai")).strftime("[%m-%d %H:%M:%S]")} ({os.path.basename(sys._getframe().f_back.f_code.co_filename)}, line{sys._getframe().f_back.f_lineno})=> {info}"', flush=flush)

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


# def init_distributed_mode(local_out_path, fork=False):
#     # os.makedirs(local_out_path, exist_ok=True)
#     try:
#         dist.initialize(fork=fork)
#         dist.barrier()
#     except RuntimeError:
#         print(f'NCCL Error! stopping training!', flush=True)
#         time.sleep(10)
#         os.system('pkill bash')
#
#     _change_builtin_print(dist.is_local_master())
#     if dist.is_local_master() and local_out_path is not None and len(local_out_path):
#         sys.stdout, sys.stderr = SyncPrint(local_out_path, sync_stdout=True), SyncPrint(local_out_path, sync_stdout=False)


def _change_builtin_print(is_master):
    import builtins as __builtin__
    
    builtin_print = __builtin__.print
    if type(builtin_print) != type(open):
        return
    
    def prt(*args, **kwargs):
        force = kwargs.pop('force', False)
        clean = kwargs.pop('clean', False)
        deeper = kwargs.pop('deeper', False)
        if is_master or force:
            if not clean:
                f_back = sys._getframe().f_back
                if deeper and f_back.f_back is not None:
                    f_back = f_back.f_back
                file_desc = f'{f_back.f_code.co_filename:24s}'[-24:]
                builtin_print(f'{time_str()} ({file_desc}, line{f_back.f_lineno:-4d})=>', *args, **kwargs)
            else:
                builtin_print(*args, **kwargs)
    
    __builtin__.print = prt


class SyncPrint(object):
    def __init__(self, local_output_dir, sync_stdout=True):
        self.sync_stdout = sync_stdout
        self.terminal_stream = sys.stdout if sync_stdout else sys.stderr
        fname = os.path.join(local_output_dir, 'b1_stdout.txt' if sync_stdout else 'b2_stderr.txt')
        self.file_stream = open(fname, 'w')
        self.file_stream.flush()
        os_system(f'ln -s {fname} /opt/tiger/run_trial/ >/dev/null 2>&1')
        self.enabled = True
    
    def write(self, message):
        self.terminal_stream.write(message)
        self.file_stream.write(message)
    
    def flush(self):
        self.terminal_stream.flush()
        self.file_stream.flush()
    
    def cancel_sync(self):
        if not self.enabled:
            return
        self.enabled = False
        self.file_stream.close()
        if self.sync_stdout:
            sys.stdout = self.terminal_stream
        else:
            sys.stderr = self.terminal_stream
    
    def __del__(self):
        self.cancel_sync()


class DistLogger(object):
    def __init__(self, lg, verbose):
        self._lg, self._verbose = lg, verbose
    
    @staticmethod
    def do_nothing(*args, **kwargs):
        pass
    
    def __getattr__(self, attr: str):
        return getattr(self._lg, attr) if self._verbose else DistLogger.do_nothing
    
    # def __del__(self):
    #     if self._lg is not None and hasattr(self._lg, 'close'):
    #         self._lg.close()


class TensorboardLogger(object):
    def __init__(self, log_dir, filename_suffix):
        from torch.utils.tensorboard import SummaryWriter
        self.writer = SummaryWriter(log_dir=log_dir, filename_suffix=filename_suffix)
        self.step = 0
    
    def set_step(self, step=None):
        if step is not None:
            self.step = step
        else:
            self.step += 1
    
    def update(self, head='scalar', step=None, **kwargs):
        for k, v in kwargs.items():
            if v is None:
                continue
            if hasattr(v, 'item'): v = v.item()
            # assert isinstance(v, (float, int)), type(v)
            if step is None:  # iter wise
                it = self.step
                if it == 0 or (it + 1) % 500 == 0:
                    self.writer.add_scalar(head + "/" + k, v, it)
            else:  # epoch wise
                ep = step
                self.writer.add_scalar(head + "/" + k, v, ep)
    
    def log_tensor_as_distri(self, tag, tensor1d, step=None):
        if step is None:  # iter wise
            step = self.step
            loggable = step == 0 or (step + 1) % 500 == 0
        else:  # epoch wise
            loggable = True
        if loggable:
            self.writer.add_histogram(tag=tag, values=tensor1d, global_step=step)
    
    def log_image(self, tag, img_chw, step=None):
        if step is None:  # iter wise
            step = self.step
            loggable = step == 0 or (step + 1) % 500 == 0
        else:  # epoch wise
            loggable = True
        if loggable:
            self.writer.add_image(tag, img_chw, step, dataformats='CHW')
    
    def flush(self):
        # time.sleep(10); print('[xxxxxxxxxxxxxxxxxxxxx] flushed')
        self.writer.flush()
    
    def close(self):
        # time.sleep(10); print('[xxxxxxxxxxxxxxxxxxxxx] closed')
        self.writer.close()


class SmoothedValue(object):
    """Track a series of values and provide access to smoothed values over a
    window or the global series average.
    """
    
    def __init__(self, window_size=30, fmt=None):
        if fmt is None:
            fmt = "{median:.4f} ({global_avg:.4f})"
        from collections import deque
        self.deque = deque(maxlen=window_size)
        self.total = 0.0
        self.count = 0
        self.fmt = fmt
    
    def update(self, value, n=1):
        self.deque.append(value)
        self.count += n
        self.total += value * n
    
    def synchronize_between_processes(self):
        """
        Warning: does not synchronize the deque!
        """
        import torch
        t = torch.tensor([self.count, self.total], dtype=torch.float64, device='cuda')
        torch.distributed.barrier()
        torch.distributed.all_reduce(t)
        t = t.tolist()
        self.count = int(t[0])
        self.total = t[1]
    
    @property
    def median(self):
        import numpy as np
        return np.median(self.deque)
    
    @property
    def avg(self):
        return sum(self.deque) / len(self.deque)
    
    @property
    def global_avg(self):
        return self.total / self.count
    
    @property
    def max(self):
        return max(self.deque)
    
    @property
    def value(self):
        return self.deque[-1]
    
    def time_preds(self, counts):
        remain_secs = counts * self.median
        remain_time = datetime.timedelta(seconds=round(remain_secs))
        finish_time = time.strftime("%m-%d %H:%M", time.localtime(time.time() + remain_secs))
        return remain_secs, str(remain_time), finish_time
    
    def __str__(self):
        return self.fmt.format(
            median=self.median,
            avg=self.avg,
            global_avg=self.global_avg,
            max=self.max,
            value=self.value)


class MetricLogger(object):
    def __init__(self, delimiter="\t"):
        from collections import defaultdict
        self.meters = defaultdict(SmoothedValue)
        self.delimiter = delimiter
    
    def update(self, **kwargs):
        for k, v in kwargs.items():
            if v is None:
                continue
            if hasattr(v, 'item'): v = v.item()
            # assert isinstance(v, (float, int)), type(v)
            self.meters[k].update(v)
    
    def __getattr__(self, attr):
        if attr in self.meters:
            return self.meters[attr]
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError("'{}' object has no attribute '{}'".format(
            type(self).__name__, attr))
    
    def __str__(self):
        loss_str = []
        for name, meter in self.meters.items():
            loss_str.append(
                "{}: {}".format(name, str(meter))
            )
        return self.delimiter.join(loss_str)
    
    def synchronize_between_processes(self):
        for meter in self.meters.values():
            meter.synchronize_between_processes()
    
    def add_meter(self, name, meter):
        self.meters[name] = meter
    
    def log_every(self, max_iters, itrt, print_freq, header=None):
        import numpy as np
        print_iters = set(np.linspace(0, max_iters-1, print_freq, dtype=int).tolist())
        if not header:
            header = ''
        start_time = time.time()
        end = time.time()
        self.iter_time = SmoothedValue(fmt='{avg:.4f}')
        self.data_time = SmoothedValue(fmt='{avg:.4f}')
        space_fmt = ':' + str(len(str(max_iters))) + 'd'
        log_msg = [
            header,
            '[{0' + space_fmt + '}/{1}]',
            'eta: {eta}',
            '{meters}',
            'time: {time}',
            'data: {data}'
        ]
        log_msg = self.delimiter.join(log_msg)
        
        if isinstance(itrt, Iterator) and not hasattr(itrt, 'preload') and not hasattr(itrt, 'set_epoch'):
            for i in range(max_iters):
                obj = next(itrt)
                self.data_time.update(time.time() - end)
                yield obj
                self.iter_time.update(time.time() - end)
                if i in print_iters:
                    eta_seconds = self.iter_time.global_avg * (max_iters - i)
                    eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
                    print(log_msg.format(
                        i, max_iters, eta=eta_string,
                        meters=str(self),
                        time=str(self.iter_time), data=str(self.data_time)))
                end = time.time()
        else:
            for i, obj in enumerate(itrt):
                self.data_time.update(time.time() - end)
                yield obj
                self.iter_time.update(time.time() - end)
                if i in print_iters:
                    eta_seconds = self.iter_time.global_avg * (max_iters - i)
                    eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
                    print(log_msg.format(
                        i, max_iters, eta=eta_string,
                        meters=str(self),
                        time=str(self.iter_time), data=str(self.data_time)))
                end = time.time()
        
        total_time = time.time() - start_time
        total_time_str = str(datetime.timedelta(seconds=int(total_time)))
        print('{}   Total time:      {}   ({:.3f} s / it)'.format(
            header, total_time_str, total_time / max_iters))
