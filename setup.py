# -*- coding:utf-8 -*-

import os
import re
from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    path = os.path.join(package, '__init__.py')
    init_py = open(path, 'r', encoding='utf8').read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_long_description():
    """
    Return the README.
    """
    return open('readme.md', 'r', encoding='utf-8').read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


requirements = [
    "fastapi=0.44.1",
]


setup(
    name='fastapi-route',
    version=get_version('route'),
    url='https://github.com/XunJinhuan/fastapi-route.git',
    description='A custom route for web framework fastapi',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='XunJinhuan',
    packages=get_packages('route'),
    install_requires=requirements,
    include_package_data=True,
)
