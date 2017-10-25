# coding=utf-8
from __future__ import unicode_literals

from unittest import TestCase
from django_selectel.storages import ApiStorage
import os
import gzip
from mock import patch
from StringIO import StringIO
import requests


class HTTPResponse(object):

    def __init__(self, content, status=200, headers={}):
        self.status_code = status
        self.status = status
        self.body = content
        self.content = content
        self.headers = headers

    def raise_for_status(self):
        if self.status >= 400 or self.status < 200:
            raise requests.exceptions.HTTPError(response=self)


class ApiSotrageTestCase(TestCase):

    def make_request(self, content, status=200, headers={}):
        def req(*args, **kwargs):
            if kwargs.get('headers', {}).get("X-Auth-Key"):
                # authenticate
                return HTTPResponse("", status=204, headers={
                    "X-Expire-Auth-Token": 3600,
                    "X-Storage-Url": "https://selectel.api.com/",
                    "X-Auth-Token": 'test_token'
                })
            else:
                return HTTPResponse(content, status, headers)
        return req

    @patch("requests.get")
    @patch("requests.Session.get")
    def test_get_file(self, session_mock, requests_mock):
        test_content = 'test_content'
        test_path = 'container/test.txt'

        requests_mock.side_effect = self.make_request(test_content)
        session_mock.side_effect = self.make_request(test_content)

        storage = ApiStorage(
            user="test",
            password="test"
        )

        fileobj = storage.open(test_path)
        self.assertEqual(fileobj.read(), test_content)
        self.assertEqual(fileobj.name, os.path.basename(test_path))

    @patch("requests.get")
    @patch("requests.Session.put")
    @patch("requests.Session.head")
    def test_save_file(self, session_mock_head, session_mock_put, requests_mock):
        test_content = 'test_content'
        test_path = 'container/test.txt'

        requests_mock.side_effect = self.make_request(test_content)
        session_mock_put.side_effect = self.make_request("", status=201)
        session_mock_head.return_value = HTTPResponse("", status=404)

        storage = ApiStorage(
            user="test",
            password="test"
        )

        path = storage.save(test_path, StringIO(test_content))
        self.assertEqual(path, test_path)

    @patch("requests.get")
    @patch("requests.Session.get")
    def test_get_file_gz(self, session_mock, requests_mock):
        test_content = 'Кирилица Cirrilic'.encode("utf-8")
        gz_file = StringIO()
        g_file_gzip = gzip.GzipFile(fileobj=gz_file, mode="wb")
        g_file_gzip.write(test_content)
        g_file_gzip.close()
        gz_file_content = gz_file.getvalue()

        test_path = 'container/test.txt'

        requests_mock.side_effect = self.make_request(gz_file_content)
        session_mock.side_effect = self.make_request(gz_file_content)

        storage = ApiStorage(
            user="test",
            password="test",
            use_gz=True
        )

        fileobj = storage.open(test_path)
        self.assertEqual(fileobj.read(), test_content)
        self.assertEqual(fileobj.name, os.path.basename(test_path))

    @patch("requests.get")
    @patch("requests.Session.head")
    def test_get_size_file(self, session_mock, requests_mock):
        size = 10000
        requests_mock.side_effect = self.make_request("")
        session_mock.side_effect = self.make_request("", headers={
            "Content-Length": size
        })

        storage = ApiStorage(
            user="test",
            password="test",
            use_gz=True
        )

        self.assertEqual(storage.size("/test/path/text.txt"), size)

    @patch("requests.get")
    @patch("requests.Session.head")
    def test_exists_file(self, session_mock, requests_mock):
        requests_mock.side_effect = self.make_request("")
        session_mock.side_effect = self.make_request("")

        storage = ApiStorage(
            user="test",
            password="test",
            use_gz=True
        )

        self.assertEqual(storage.exists("/test/path/text.txt"), True)
        session_mock.side_effect = self.make_request("", status=404)
        self.assertEqual(storage.exists("/test/path/text.txt"), False)
