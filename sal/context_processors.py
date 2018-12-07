from django.conf import settings  # import the settings file
import plistlib
import os

from server.utils import get_server_version


SAL_VERSION = get_server_version()


def display_name(request):
    return {'DISPLAY_NAME': settings.DISPLAY_NAME}


def config_installed(request):
    return {'CONFIG_INSTALLED': True if 'config' in settings.INSTALLED_APPS else False}


def sal_version(request):
    return {'SAL_VERSION': SAL_VERSION}
