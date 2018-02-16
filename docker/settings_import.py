#!/usr/bin/python
from os import getenv
import locale
from system_settings import *

# Read the DEBUG setting from env var
try:
    if getenv('DOCKER_SAL_DEBUG').lower() == 'true':
        DEBUG = True
    else:
        DEBUG = False
except Exception:
    DEBUG = False


# Read the BASIC_AUTH setting from env var
try:
    if getenv('DOCKER_SAL_BASIC_AUTH').lower() == 'true':
        BASIC_AUTH = True
    else:
        BASIC_AUTH = False
except Exception:
    BASIC_AUTH = True

# TODO: Use utility to set database setting?
# Path to a root ca
try:
    if getenv('DOCKER_SAL_ROOT_CA'):
        ROOT_CA = getenv('DOCKER_SAL_ROOT_CA')
    else:
        ROOT_CA = None
except Exception:
    ROOT_CA = None

# Read list of admins from $DOCKER_SAL_ADMINS env var
admin_list = []
if getenv('DOCKER_SAL_ADMINS'):
    admins_var = getenv('DOCKER_SAL_ADMINS')
    if ',' in admins_var and ':' in admins_var:
        for admin in admins_var.split(':'):
            admin_list.append(tuple(admin.split(',')))
        ADMINS = tuple(admin_list)
    elif ',' in admins_var:
        admin_list.append(tuple(admins_var.split(',')))
        ADMINS = tuple(admin_list)
else:
    ADMINS = []

# Read the preferred time zone from $DOCKER_SAL_TZ, use system locale or
# set to 'America/New_York' if neither are set
if getenv('DOCKER_SAL_TZ'):
    if '/' in getenv('DOCKER_SAL_TZ'):
        TIME_ZONE = getenv('DOCKER_SAL_TZ')
    else:
        TIME_ZONE = 'Europe/London'
# elif getenv('TZ'):
#     TIME_ZONE = getenv('TZ')
# else:
#     TIME_ZONE = 'America/New_York'

# Read the preferred language code from $DOCKER_SAL_LANG, use system locale or
# set to 'en_US' if neither are set
if getenv('DOCKER_SAL_LANG'):
    if '_' in getenv('DOCKER_SAL_LANG'):
        LANGUAGE_CODE = getenv('DOCKER_SAL_LANG')
    else:
        LANGUAGE_CODE = 'en_US'
# elif locale.getdefaultlocale():
#     LANGUAGE_CODE = locale.getdefaultlocale()[0]
else:
    LANGUAGE_CODE = 'en_US'

# Read the list of allowed hosts from the $DOCKER_SAL_ALLOWED env var, or
# allow all hosts if none was set.
if getenv('DOCKER_SAL_ALLOWED'):
    ALLOWED_HOSTS = getenv('DOCKER_SAL_ALLOWED').split(',')
else:
    ALLOWED_HOSTS = ['*']

# Set the display name from the $DOCKER_SAL_DISPLAY_NAME env var, or
# use the default
if getenv('DOCKER_SAL_DISPLAY_NAME'):
    DISPLAY_NAME = getenv('DOCKER_SAL_DISPLAY_NAME')
else:
    DISPLAY_NAME = 'Sal'

# Set the default machine group key from the $DOCKER_SAL_DEFAULT_MACHINE_GROUP_KEY env var, or
# use the default (unassigned)
if getenv('DOCKER_SAL_DEFAULT_MACHINE_GROUP_KEY'):
    DEFAULT_MACHINE_GROUP_KEY = getenv('DOCKER_SAL_DEFAULT_MACHINE_GROUP_KEY')
else:
    DEFAULT_MACHINE_GROUP_KEY = None

try:
    if getenv('DOCKER_SAL_ADD_TO_ALL_BUSINESS_UNITS').lower() == 'true':
        ADD_TO_ALL_BUSINESS_UNITS = True
    else:
        ADD_TO_ALL_BUSINESS_UNITS = False
except Exception:
    ADD_TO_ALL_BUSINESS_UNITS = False

# TODO: Use utility to set database setting?
try:
    if getenv('DOCKER_SAL_CRYPT_URL'):
        CRYPT_URL = getenv('DOCKER_SAL_CRYPT_URL')
    else:
        CRYPT_URL = None
except Exception:
    CRYPT_URL = None


# Read the SSH_ACCOUNT setting from env var
try:
    if getenv('DOCKER_SAL_SSH_ACCOUNT'):
        SSH_ACCOUNT = getenv('DOCKER_SAL_SSH_ACCOUNT')
    else:
        SSH_ACCOUNT = None
except Exception:
    SSH_ACCOUNT = None

# Do machines turn to 'deployed' when they check in?
try:
    if getenv('DOCKER_SAL_DEPLOYED_ON_CHECKIN').lower() == 'true':
        DEPLOYED_ON_CHECKIN = True
    else:
        DEPLOYED_ON_CHECKIN = False
except Exception:
    DEPLOYED_ON_CHECKIN = False

# How long until machines are inactive before they are considered undeployed?
try:
    INACTIVE_UNDEPLOYED = int(getenv('DOCKER_SAL_INACTIVE_UNDEPLOYED'))
except Exception:
    INACTIVE_UNDEPLOYED = 0
