#!/usr/bin/python3
# Copyright (C) 2022 Keyu Tian. All rights reserved.
import argparse
import glob
import os
import re
import sys
from functools import partial

import chardet

from toolky.core import to_parallelize, mt_thread, cpu_count

__all__ = ['main']


def find(f_name, regex, key_str):
    num_lines = 0
    try:
        with open(f_name, 'rb') as fp:
            byte_data = fp.read()
        if len(byte_data) == 0:
            return 0
        lines = byte_data.decode(chardet.detect(byte_data).get('encoding', 'utf-8')).splitlines()
        contains = []
        for i, line in enumerate(lines):
            num_lines += 1
            if regex.match(line) is not None:
                contains.append(i + 1)
        if len(contains) != 0:
            sys.stdout.write(f'`{key_str}\' found in  {f_name:24s}:  [line {str(contains).strip("[]")}]\n')
    except Exception as e:
        sys.stderr.write(f'[{f_name}: file read err ({type(e)})]\n')
        # raise e

    return num_lines


@mt_thread(10)
def mp_find(file_name, regex, key_str):
    return find(file_name, regex, key_str)


def main():
    DIR_IGNORED = {'__pycache__', '__pypackages__', '.git', '.idea'}
    TARGET_POSTFIX = {
        'c', 'cc', 'cpp', 'cxx', 'cs', 'h', 'hpp', 'f', 'for',
        'py', 'java', 'kt', 'm',
        'js', 'ts', 'html', 'css', 'php',
        'yaml', 'sh',
        'json', 'txt', 'md',
    }
    
    gg = partial(glob.glob, recursive=True)
    ggi = partial(glob.iglob, recursive=True)
    
    desc = 'Search for some texts. [Example:  %(prog)s  "./dir/*.py"  "torch.*fft"  "3\\*3 == 9" ]'
    parser = argparse.ArgumentParser(prog='sea', description=desc)
    parser.add_argument('position', metavar='D/F', type=str, nargs='?', help='directory name or file name to be searched (wildcard * and ** is supported; default: cwd `.`)', default='./')
    parser.add_argument('keys', metavar='K', type=str, nargs='+', help='keys to search (wildcard * is supported)')
    parser.add_argument('-mp', '--mp', action='store_true', help='with multiprocessing')
    parser.add_argument('-nr', '--nr', action='store_true', help='not recursively')
    args = parser.parse_args()

    if args.position == '/':
        raise AttributeError('search from the root would be too costly!')
    
    dirs_and_files, keys = gg(os.path.expanduser(args.position)), args.keys

    files = set()
    for df in dirs_and_files:
        if os.path.isdir(df) and df not in DIR_IGNORED:
            f = filter(os.path.isfile, ggi(os.path.join(df, '**', '*')))
            files.update(set(f))
        elif os.path.isfile(df):
            files.add(df)

    files = sorted(filter(lambda fname: fname.split('.')[-1].lower() in TARGET_POSTFIX, files))
    key_str = ' | '.join(keys)
    
    t_keys = []
    s = chr(92)
    rand = 'uaweuyyawebubhdyugsaJYuaweiluidnuaeiu'
    for key in keys:
        key = key.replace(f'{s}*', rand)
        for ch in [s, '.', '^', '$', '*', '+', '?', '[', ']', '|', '{', '}', '(', ')']:
            key = key.replace(ch, s + ch)
        key = key
        t_keys.append(key)
    ks = [f'(.*{tk.replace("*", ".*").replace(rand, f"{s}*")})' for tk in t_keys]
    regex = re.compile('|'.join(ks))
    
    mp = args.mp or to_parallelize(len(files), 100)
    if mp:
        lines = mp_find([(f, regex, key_str) for f in files])
    else:
        lines = [find(f, regex, key_str) for f in files]
    
    print(f'\n[in {args.position}] #files: {len(files)}, #lines: {sum(lines)}' + (f' (w/ mt{cpu_count()})' if mp else ''))


if __name__ == '__main__':
    main()
