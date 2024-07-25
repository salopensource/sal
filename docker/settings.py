# Django settings for sal project.
from sal.system_settings import *
from sal.settings_import import *


DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': os.path.join(PROJECT_DIR, 'db/sal.db'),
        'USER': '',  # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
    }
}

# Memcached
if 'MEMCACHED_PORT_11211_TCP_ADDR' in os.environ:
    addr = os.environ['MEMCACHED_PORT_11211_TCP_ADDR']
    port = os.environ['MEMCACHED_PORT_11211_TCP_PORT']
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [f"{addr}:{port}", '11211']
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

if 'AWS_IAM' in os.environ:
    import requests
    cert_bundle_url = 'https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem'
    cert_target_path = '/etc/ssl/certs/global-bundle.pem'

    response = requests.get(cert_bundle_url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(cert_target_path), exist_ok=True)

        with open(cert_target_path, 'wb') as file:
            file.write(response.content)
        print(f"AWS RDS cert bundle successfully downloaded and saved to {cert_target_path}")
    else:
        print(f"Failed to download AWS RDS cert bundle, status code: {response.status_code}")
    DATABASES = {
        'default': {
            'ENGINE': 'django_iam_dbauth.aws.postgresql',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'HOST': os.environ['DB_HOST'],
            'PORT': os.environ['DB_PORT'],
            'OPTIONS' : {
                'region_name': os.environ['AWS_RDS_REGION'],
                'sslmode': 'verify-full',
                'sslrootcert': '/etc/ssl/certs/global-bundle.pem',
                'use_iam_auth': True,
            }
        }
    }
