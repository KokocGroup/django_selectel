# coding=utf-8
from __future__ import unicode_literals

import logging

try:
    from django.conf import settings as django_settings
except ImportError:
    logging.warning("Django not installed")
    django_settings = None


SELECTEL_STORAGE = {
    "USER": None,
    "PASSWORD": None,
    "DOMAINS": {},
    "OVERWRITE_FILES": False,
    "USE_GZ": False,
    "AUTH_URL": "https://auth.selcdn.ru/",
    "API_THRESHOLD": 30 * 60,
    "API_MAX_RETRY": 3,
    "API_RETRY_DELAY": 0.1
}

if hasattr(django_settings, "SELECTEL_STORAGE"):
    SELECTEL_STORAGE.update(django_settings.SELECTEL_STORAGE)
