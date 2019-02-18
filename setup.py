# coding=utf-8

import os
import re

from setuptools import setup

try:
    from pypandoc import convert

    def read_md(f):
        return convert(f, 'rst')
except ImportError:
    def read_md(f):
        return open(f, 'r').read()


def get_packages(package):
    return [dirpath.replace(os.path.sep, ".")
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]
    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


def get_version(package):
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('django_selectel')


setup(
    name='django_selectel',
    description="The file store in the Selectel cloud store for Django",
    long_description=read_md('README.md'),
    version=version,
    download_url='https://github.com/KokocGroup/django_selectel/tarball/v{}'.format(version),
    license='BSD',
    url='https://github.com/KokocGroup/django_selectel',
    packages=get_packages('django_selectel'),
    author='KokocGroup',
    author_email='dev@kokoc.com',
    install_requires=[
        'requests==2.18.4'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
