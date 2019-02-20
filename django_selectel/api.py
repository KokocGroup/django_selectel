# coding=utf-8
from __future__ import unicode_literals

import hashlib
import logging
import os
import time
import utils

from datetime import datetime
from datetime import timedelta
from functools import wraps

import requests


class SelectelCDNApiException(Exception):

    def __init__(self, message, *args, **kwargs):
        message = "Selectel: {}".format(message)
        self.response = kwargs.pop('response', None)
        super(SelectelCDNApiException, self).__init__(message)


class SelectelCDNApi(object):

    def __init__(self, user, password, auth_url, threshold=None, max_retry=None, retry_delay=None):
        self.user = user
        self.password = password
        self.auth_url = auth_url
        self.threshold = threshold or 0
        self.max_retry = max_retry
        self.retry_delay = retry_delay

        self._token_expire_dt = None
        self._storage_url = None
        self._session = None
        self.logger = logging.getLogger("SelectelApi")

    def update_expired_token(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self.is_token_expire:
                self.authenticate()
            try:
                return fn(self, *args, **kwargs)
            except (requests.exceptions.HTTPError, SelectelCDNApiException) as e:
                if e.response.status_code == 401:
                    self.authenticate()
                    return fn(self, *args, **kwargs)
                else:
                    raise e

        return wrapper

    def attempts(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self.max_retry is not None:
                retries = self.max_retry
                while retries > 1:
                    try:
                        return fn(self, *args, **kwargs)
                    except (requests.exceptions.HTTPError, SelectelCDNApiException):
                        retries -= 1
                        time.sleep(self.retry_delay)
            return fn(self, *args, **kwargs)

        return wrapper

    @property
    def is_token_expire(self):
        if not self._token_expire_dt:
            return True

        return (self._token_expire_dt - datetime.now()).total_seconds() < self.threshold

    @update_expired_token
    def get_url(self, container, path):
        return os.path.join(self._storage_url, container, path)

    def authenticate(self):
        if not self.user or not self.password:
            raise SelectelCDNApiException("Not set user or password")
        headers = {
            "X-Auth-User": self.user,
            "X-Auth-Key": self.password
        }
        r = requests.get(self.auth_url, headers=headers, verify=True)
        if r.status_code != 204:
            raise SelectelCDNApiException("Authenticate error ({})".format(r.status_code))

        self._token_expire_dt = datetime.now() + timedelta(seconds=int(r.headers['X-Expire-Auth-Token']))
        self._storage_url = r.headers['X-Storage-Url'][:-1]

        self._session = requests.Session()
        self._session.headers.update({
            "X-Auth-Token": r.headers['X-Auth-Token']
        })

    @attempts
    @update_expired_token
    def get(self, container, path, headers=None):
        url = os.path.join(self._storage_url, container, path)
        if headers is None:
            headers = {}
        response = self._session.get(url, headers=headers, verify=True)

        self.logger.info("Request GET {} - {}".format(url, response.status_code))
        try:
            response.raise_for_status()
        except Exception as e:
            raise SelectelCDNApiException("Error get file {}: {}".format(url, str(e)), response=response)
        return response.content

    @attempts
    @update_expired_token
    def get_steam(self, container, path, headers=None, chunk=2 ** 20):
        url = os.path.join(self._storage_url, container, path)
        if headers is None:
            headers = {}
        r = self._session.get(url, headers=headers, stream=True, verify=True)
        self.logger.info("Request GET_STEAM {} - {}".format(url, r.status_code))
        try:
            r.raise_for_status()
        except Exception as e:
            raise SelectelCDNApiException("Error get file {}: {}".format(url, str(e)), response=r)
        return r.iter_content(chunk_size=chunk)

    @attempts
    @update_expired_token
    def remove(self, container, path, force=False):
        url = os.path.join(self._storage_url, container, path)
        r = self._session.delete(url, verify=True)
        self.logger.info("Request REMOVE {} - {}".format(url, r.status_code))
        if force:
            if r.status_code == 404:
                return r.headers
        try:
            r.raise_for_status()
            assert r.status_code == 204
        except Exception as e:
            raise SelectelCDNApiException("Error remove file {}: {}".format(url, str(e)), response=r)
        return r.headers

    @attempts
    @update_expired_token
    def put(self, container, path, content, headers=None):
        url = os.path.join(self._storage_url, container, path)
        if headers is None:
            headers = {}
        if utils.is_py3():
             etag = hashlib.md5(content.encode('utf8') if hasattr(content, 'encode') else content).hexdigest()
        else:
            etag = hashlib.md5(content).hexdigest()
        headers["ETag"] = etag
        r = self._session.put(url, data=content, headers=headers, verify=True)
        self.logger.info("Request PUT {} - {}: {}".format(url, r.status_code, r.content))
        try:
            r.raise_for_status()
            assert r.status_code == 201
        except Exception as e:
            raise SelectelCDNApiException("Error create file {}: {}".format(url, str(e)), response=r)
        return True

    @attempts
    @update_expired_token
    def exist(self, container, path):
        url = os.path.join(self._storage_url, container, path)

        r = self._session.head(url)
        self.logger.info("Request EXIST {} - {}: {}".format(url, r.status_code, r.content))
        if r.status_code not in (200, 404):
            r.raise_for_status()
        return r.status_code == 200

    @attempts
    @update_expired_token
    def size(self, container, path):
        url = os.path.join(self._storage_url, container, path)
        r = self._session.head(url)
        self.logger.info("Request SIZE {} - {}: {}".format(url, r.status_code, r.content))
        r.raise_for_status()
        if r.status_code != 200:
            raise SelectelCDNApiException("file {} not exists".format(os.path.sep.join([container, path])), response=r)
        return int(r.headers['Content-Length'])
