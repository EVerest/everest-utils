#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright Pionix GmbH and Contributors to EVerest
#
"""
author: kai-uwe.hermann@pionix.de
Use edm to create a snapshot of the current directory without polluting the current working dir
"""

import argparse
import json
import os
import re
import yaml
import subprocess
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(
        description='create an isolated snapshot with edm')

    parser.add_argument('--working-dir', '-wd', type=str,
                        help='Working directory containing the EVerest workspace (default: .)', default=str(Path.cwd()))
    parser.add_argument('--temp-dir', '-td', type=str,
                        help='Temporary directory for creating the snapshot in (default: working-dir/tmp-for-snapshot)', default=None)

    args = parser.parse_args()

    working_dir = Path(args.working_dir).expanduser().resolve()

    tmp_dir = working_dir / 'tmp-for-snapshot'

    if args.temp_dir:
        tmp_dir = Path(args.temp_dir).expanduser().resolve()

    if working_dir == tmp_dir:
        print(f'Temporary directory cannot be equal to working directory: {tmp_dir}')
        return 1

    if tmp_dir.is_relative_to(working_dir) and tmp_dir.parent != working_dir:
        print(f'Temporary directory cannot be relative to working directory: {tmp_dir}')
        return 1

    if tmp_dir.exists():
        print(f'Temporary directory dir already exists, deleting it: {tmp_dir}')
        shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir()

    subdirs = list(working_dir.glob('*/'))
    for subdir in subdirs:
        subdir_path = Path(subdir)
        if not subdir_path.is_dir():
            print(f'{subdir_path} is not a dir, ignoring')
            continue
        if subdir_path == tmp_dir:
            print(f'{subdir_path} is tmp dir, ignoring')
            continue
        print(f'Copying {subdir_path} to {tmp_dir}')
        destdir = tmp_dir / subdir_path.name

        shutil.copytree(subdir_path, destdir, ignore=shutil.ignore_patterns('build*'))

    print('Running edm snaphot --recursive')
    with subprocess.Popen(['edm', 'snapshot', '--recursive'],
                          stderr=subprocess.PIPE, cwd=tmp_dir) as edm:
        for line in edm.stderr:
            print(line.decode('utf-8'), end='')

if __name__ == '__main__':
    main()
