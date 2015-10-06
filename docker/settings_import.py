#!/usr/bin/python
from os import getenv
import locale

# Read the DEBUG setting from env var
try:
    if getenv('DOCKER_SAL_DEBUG').lower() == 'true':
        DEBUG = True
    else:
        DEBUG = False
except:
    DEBUG = False

# Read the Brute force protection setting from env var
try:
    if getenv('DOCKER_SAL_BRUTE_PROTECT').lower() == 'true':
        BRUTE_PROTECT = True
    else:
        BRUTE_PROTECT = False
except:
    BRUTE_PROTECT = False

# Read the Brute force protection timeout setting from env var
try:
    BRUTE_COOLOFF = int(getenv('DOCKER_SAL_BRUTE_COOLOFF'))
except:
    BRUTE_COOLOFF = 3

# Read the Brute force protection limit setting from env var
try:
    BRUTE_LIMIT = int(getenv('DOCKER_SAL_BRUTE_LIMIT'))
except:
    BRUTE_LIMIT = 3

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
    ADMINS = (
                ('Admin User', 'admin@test.com')
             )

# Read the preferred time zone from $DOCKER_SAL_TZ, use system locale or
# set to 'America/New_York' if neither are set
if getenv('DOCKER_SAL_TZ'):
    if '/' in getenv('DOCKER_SAL_TZ'):
        TIME_ZONE = getenv('DOCKER_SAL_TZ')
    else: TIME_ZONE = 'Europe/London'
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
