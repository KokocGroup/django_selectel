# coding=utf-8
from __future__ import unicode_literals

from fabric.api import local, task, quiet


def change_version(change):
    version_row = local("grep '__version__ = ' django_selectel/__init__.py", capture=True)
    version = version_row.split(' = ')[1].strip()
    version = map(int, version[1:-1].split('.'))
    new_version = '.'.join(map(str, change(*version)))
    local("sed -i -- 's/__version__ =.*/__version__ = \"{}\"/g' django_selectel/__init__.py".format(new_version))
    return new_version


def release(new_version):
    with quiet():
        local('git commit -am "new version {}"'.format(new_version))
        local('git tag -a v{0} -m \'new version {0}\''.format(new_version))
        local('git push origin master --tags')
    local("python setup.py register")
    local("python setup.py sdist upload -r https://upload.pypi.org/legacy/")


@task
def major():
    release(change_version(lambda x, y, z: [x+1, 0, 0]))


@task
def minor():
    release(change_version(lambda x, y, z: [x, y+1, 0]))


@task
def patch():
    release(change_version(lambda x, y, z: [x, y, z+1]))


@task
def tests():
    local('python -m unittest discover')
