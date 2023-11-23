# Copyright (C) 2022 Keyu Tian. All rights reserved.
import os
import threading
from functools import wraps
from multiprocessing import Pool as ProcPool
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from os import getpid

"""
from https://stackoverflow.com/questions/46045956/whats-the-difference-between-threadpool-vs-pool-in-the-multiprocessing-module
The rule of thumb is:
- IO bound jobs -> multiprocessing.pool.ThreadPool
- CPU bound jobs -> multiprocessing.Pool
- Hybrid jobs -> depends on the workload, I usually prefer the multiprocessing.Pool due to the advantage process isolation brings
"""
__all__ = ['CPU_COUNT', 'need_parallelize', 'getpid', 'gettid', 'mt_proc', 'mt_thread']


CPU_COUNT = int(os.getenv('ARNOLD_WORKER_CPU', cpu_count()))


def need_parallelize(num_tasks, ratio):
    cores = int(os.getenv('ARNOLD_WORKER_CPU', cpu_count()))
    return cores >= 4 and num_tasks > ratio * cores


def mt_proc(threads=0, chunksize=1):
    def decorator(func):
        @wraps(func)
        def wrapper(arg_list):
            with ProcPool(threads or CPU_COUNT) as pool:
                rets = list(pool.starmap(func, arg_list, chunksize=chunksize))
            return rets
        return wrapper
    
    return decorator


def mt_thread(threads=0, chunksize=1):
    def decorator(func):
        @wraps(func)
        def wrapper(arg_list):
            with ThreadPool(threads or CPU_COUNT) as pool:
                rets = list(pool.starmap(func, arg_list, chunksize=chunksize))
            return rets
        return wrapper
    
    return decorator


def gettid(naive=True):
    return threading.get_native_id() if naive else threading.get_ident()

