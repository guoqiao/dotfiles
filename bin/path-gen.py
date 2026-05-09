#!/usr/bin/env python3
"""Generate $PATH for your system.
"""

import os
import sys
from pathlib import Path

def get_sub_paths(parent, *subdirs):
    # /usr/local, bin, sbin -> /usr/local/bin, /usr/local/sbin
    if os.path.exists(parent):
        return [f"{parent}/{subdir}" for subdir in subdirs]
    else:
        return []


PATH = [
    '~/.dot/bin',
    '~/.dot/.venv/bin',
    '~/bin',
    '~/.local/bin',
    '~/.npm-global/bin',
    '~/.amp/bin',
    '~/.bun/bin',
    '~/.cargo/bin',
    '~/.orbstack/bin',
    '~/.browser-use-env/bin',
    *get_sub_paths('/home/linuxbrew/.linuxbrew', 'bin', 'sbin'),
    *get_sub_paths('/opt/homebrew', 'bin', 'sbin'),
    '/usr/local/cuda/bin',
]

valid_paths = []

for path in PATH:
    real_path = Path(path).expanduser().resolve()
    # print(f"{path} -> {real_path}")
    if real_path.is_dir():
        if real_path not in valid_paths:
            valid_paths.append(path)  # let's still add the orignal str, e.g.: ~/bin

PATH = ':'.join([str(p) for p in valid_paths])
# add a new line at end
line = f'export PATH={PATH}:$PATH\n'
print(line)
