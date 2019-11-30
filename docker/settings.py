# Django settings for sal project.
from sal.system_settings import *
from sal.settings_import import *

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': os.path.join(PROJECT_DIR, 'db/sal.db'),
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Memcached
if 'MEMCACHED_PORT_11211_TCP_ADDR' in os.environ:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [
                '%s:%s' % (os.environ['MEMCACHED_PORT_11211_TCP_ADDR'],
                           os.environ['MEMCACHED_PORT_11211_TCP_PORT'], '11211'),
            ]
        }
    }

# PG Database
host = None
port = None

if 'DB_USER' in os.environ:
    if 'DB_HOST' in os.environ:
        host = os.environ.get('DB_HOST')
        port = os.environ.get('DB_PORT', '5432')

    elif 'DB_PORT_5432_TCP_ADDR' in os.environ:
        host = os.environ.get('DB_PORT_5432_TCP_ADDR')
        port = os.environ.get('DB_PORT_5432_TCP_PORT', '5432')

    else:
        host = 'db'
        port = '5432'

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
