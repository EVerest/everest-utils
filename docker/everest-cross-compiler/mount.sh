#!/bin/bash
sudo mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc || true
bash
