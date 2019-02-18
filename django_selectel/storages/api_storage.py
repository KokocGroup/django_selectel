# coding=utf-8
from __future__ import unicode_literals

import gzip
import os

from django.core.files import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django_selectel import settings
from django_selectel.api import SelectelCDNApi
from django_selectel import utils


if utils.is_py3():
    from io import StringIO, BytesIO
else:
    from StringIO import StringIO


class ApiStorageException(Exception):
    pass


@deconstructible
class ApiStorage(Storage):

    def __init__(self, user=None, password=None, domains=None, overwrite_files=None, use_gz=None):

        self.user = user or settings.SELECTEL_STORAGE.get("USER")

        if not self.user:
            raise ApiStorageException('The "USER" parameter in the SELECTEL_STORAGE settings is not passed or set')

        self.password = password or settings.SELECTEL_STORAGE.get('PASSWORD')

        if not self.password:
            raise ApiStorageException('The "PASSWORD" parameter in the SELECTEL_STORAGE settings is not passed or set')

        self.domains = domains if domains is not None else settings.SELECTEL_STORAGE.get('DOMAINS', {})

        self.overwrite_files = overwrite_files if overwrite_files is not None else settings.SELECTEL_STORAGE.get("OVERRIDE_FILES", False)
        self.use_gz = use_gz if use_gz is not None else settings.SELECTEL_STORAGE.get("USE_GZ", False)

        self._api = SelectelCDNApi(
            user=self.user,
            password=self.password,
            auth_url=settings.SELECTEL_STORAGE['AUTH_URL'],
            threshold=settings.SELECTEL_STORAGE['API_THRESHOLD'],
            max_retry=settings.SELECTEL_STORAGE['API_MAX_RETRY'],
            retry_delay=settings.SELECTEL_STORAGE['API_RETRY_DELAY']
        )

    def get_available_name(self, name, max_length=None):
        if not self.overwrite_files:
            return super(ApiStorage, self).get_available_name(name, max_length)
        return name

    def _parse_path(self, path):
        splited_path = path.split(os.path.sep)
        if len(splited_path) > 1:
            return splited_path[0], os.path.sep.join(splited_path[1:])
        return splited_path[0], ""

    def path(self, name):
        return name

    def exists(self, name):
        container, path = self._parse_path(name)
        return self._api.exist(container, path)

    def size(self, name):
        container, path = self._parse_path(name)
        return self._api.size(container, path)

    def url(self, name):
        container, path = self._parse_path(name)
        if settings.SELECTEL_STORAGE.get('DOMAINS', {}).get(container):
            return os.path.join(settings.SELECTEL_STORAGE["DOMAINS"][container], path)
        return self._api.get_url(container, path)

    def delete(self, name):
        container, path = self._parse_path(name)
        self._api.remove(container, path)

    def _save(self, name, content):
        container, path = self._parse_path(name)
        if hasattr(content.file, 'seek'):
            content.file.seek(0)

        if self.use_gz:
            g_file = StringIO()
            g_file_gzip = gzip.GzipFile(fileobj=g_file, mode="wb")
            g_file_gzip.write(content.read())
            g_file_gzip.close()
            file_content = g_file.getvalue()
        else:
            file_content = content.read()
        self._api.put(container, path, file_content)
        return name

    def _open(self, name, mode='rb'):
        return SelectelCDNFile(self, name)

    def _read(self, name):
        container, path = self._parse_path(name)
        content = self._api.get(container, path)
        return content


class SelectelCDNFile(File):

    def __init__(self, storage, path):
        self._storage = storage
        self._path = path
        self._content = None
        self._file = None
        self._is_dirty = False

    @cached_property
    def content(self):
        content = self.read()
        self.seek(0)
        return content

    def open(self, mode=None):
        self.seek(0)

    @property
    def name(self):
        return os.path.basename(self._path)

    @cached_property
    def size(self):
        return self._storage.size(self._path)

    @property
    def file(self):
        if not self._file:
            content = self._storage._read(self._path)
            if self._storage.use_gz:
                content_obj = StringIO(content)
                content_obj.seek(0)
                content = gzip.GzipFile(fileobj=content_obj, mode='rb').read()
            if utils.is_py3() and isinstance(content, bytes):
                self._file = BytesIO(content)
            else:
                self._file = StringIO(content)
            
            self._file.seek(0)
        return self._file

    def readlines(self):
        return self.file.readlines()

    def read(self, num_bytes=None):
        if num_bytes:
            return self.file.read(num_bytes)
        else:
            return self.file.read()

    def write(self, content):
        self.file.write(content)
        self._is_dirty = True

    def close(self):
        if self._is_dirty:
            self._storage.save(self.name, self)
        self.file.close()
