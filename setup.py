#!/usr/bin/env python
# coding: utf-8


from setuptools import setup
import os
import re

cur_dir = os.path.dirname(__file__)
src_dir = 'revo-export'

py_modules = []
for fname in os.listdir(os.path.join(cur_dir, src_dir)):
    m = re.match("(.*)\.py$", fname)
    if m:
        py_modules.append(m.group(1))
        
setup(
    name = "revo-export",
    version = 1,

    package_dir = {'': src_dir},
    py_modules = py_modules,
)
