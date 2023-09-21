# Copyright (C) 2023 Keyu Tian. All rights reserved.

import os
import re

from toolky.misc import os_system

def get_bns(): return re.findall(f"'name':[^']*'([^']*)", os.environ['ARNOLD_BYTENAS_VOLUMES'])
def get_bns_must_start_with(prefix='tky'): return re.findall(f"'name':[^']*'((?={prefix})[^']*)", os.environ['ARNOLD_BYTENAS_VOLUMES'])
def get_bns_not_starts_with(prefix='tky'): return re.findall(f"'name':[^']*'((?!{prefix})[^']*)", os.environ['ARNOLD_BYTENAS_VOLUMES'])
def nas_touch(bn): os_system(f'/opt/tiger/nastk/bin/nastk warmup file://{bn}')
