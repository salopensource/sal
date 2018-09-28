from django.conf import settings  # import the settings file
import plistlib
import os


def display_name(request):
    # return the value you want as a dictionary. you may add multiple values in there.
    return {'DISPLAY_NAME': settings.DISPLAY_NAME}


def config_installed(request):
    if 'config' in settings.INSTALLED_APPS:
        return {'CONFIG_INSTALLED': True}

    else:
        return {'CONFIG_INSTALLED': False}


def sal_version(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, 'version.plist'), 'rb') as handle:
        version = plistlib.load(handle)
    return {'SAL_VERSION': version['version']}
