#!/usr/bin/env python3
"""
rename files in batch in place.

usage:
./vimv.py
"""

import sys
import argparse
import subprocess
import os
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

FILE = Path(__file__)
LOG = logging.getLogger(FILE.stem)


parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="print verbose logs")
parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true", help="dry run")
parser.add_argument('paths', metavar='PATH', nargs='*', help='file or dir paths to rename')

args = parser.parse_args()
logging.basicConfig(level=["INFO", "DEBUG"][args.verbose])

dry_run = args.dry_run

PATHS = args.paths or ["."]
LOG.debug(PATHS)


def read_text(filename):
    with open(filename, mode='r') as f:
        return f.read()


def read_lines(filename):
    # read valid lines, exclude comments
    lines = []
    with open(filename, mode='r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
    return lines


files = set()

for p in PATHS:
    if os.path.isdir(p):
        files |= set(os.listdir(p))
    elif os.path.isfile(p):
        files.add(p)

files = sorted(files)
text = os.linesep.join(files)

# write file list into src file
srcfile = NamedTemporaryFile(mode='w+', delete=False, prefix='src_')
srcfilename = srcfile.name
LOG.debug(srcfilename)
srcfile.write(text)
srcfile.close()

#subprocess.call(['vim', srcfilename])

# also write file list into dst file
dstfile = NamedTemporaryFile(mode='w+', delete=False, prefix='dst_')
dstfilename = dstfile.name
LOG.debug(dstfilename)
dstfile.write(text)
dstfile.close()

# now you can edit src and dst side by side
subprocess.call(['vim', '-O', srcfilename, dstfilename])

srcfilelines = read_lines(srcfilename)
dstfilelines = read_lines(dstfilename)

if len(srcfilelines) != len(dstfilelines):
    sys.exit('ERROR: src and dst file number mismatch, exit')


print("files to rename:")
tasks = []
for old, new in zip(srcfilelines, dstfilelines):
    if old != new:
        print('"{}" -> "{}"'.format(old, new))
        tasks.append((old, new))

total = len(tasks)
if total == 0:
    sys.exit('no file to rename, exit')

done = 0
answer = input(f'Are you sure to rename above {total} files? [Yn]') or 'y'
if answer.lower() == 'y':
    for old, new in tasks:
        if not dry_run:
            os.rename(old, new)
            done += 1

print(f'{done} files renamed')
