# Django settings for sal project.
from system_settings import *
from settings_import import ADMINS, TIME_ZONE, LANGUAGE_CODE, ALLOWED_HOSTS, DISPLAY_NAME, DEFAULT_MACHINE_GROUP_KEY,DEBUG, BRUTE_PROTECT, BRUTE_COOLOFF, BRUTE_LIMIT

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_DIR, 'db/sal.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Memcached
if os.environ.has_key('MEMCACHED_PORT_11211_TCP_ADDR'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [
                '%s:%s' % (os.environ['MEMCACHED_PORT_11211_TCP_ADDR'], os.environ['MEMCACHED_PORT_11211_TCP_PORT']),
            ]
        }
    }

# PG Database
host = None
port = None

if os.environ.has_key('DB_HOST'):
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')

elif os.environ.has_key('DB_PORT_5432_TCP_ADDR'):
    host = os.environ.get('DB_PORT_5432_TCP_ADDR')
    port = os.environ.get('DB_PORT_5432_TCP_PORT', '5432')

if host and port:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASS'],
            'HOST': host,
            'PORT': port,
        }
    }

if BRUTE_PROTECT==True:
    INSTALLED_APPS+= ('axes',)
    MIDDLEWARE_CLASSES+=('axes.middleware.FailedLoginMiddleware',)
