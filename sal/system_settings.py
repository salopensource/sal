import os
DEBUG = False
APPEND_SLASH = True
PROJECT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
            ), os.path.pardir))
PLUGIN_DIR = os.path.join(PROJECT_DIR, 'plugins')
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

AUTH_PROFILE_MODULE = "sal.UserProfile"
DISPLAY_NAME = 'Sal'
MANAGERS = ADMINS
CRYPT_URL = None
DEPLOYED_ON_CHECKIN = False
INACTIVE_UNDEPLOYED = 0

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates'),
            os.path.join(PROJECT_DIR, 'server', 'plugins'),
            PLUGIN_DIR,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                 'django.template.context_processors.debug',
                 'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sal.context_processors.display_name',
                'sal.context_processors.sal_version',
            ],
            'debug': DEBUG,
            'autoescape': False,
        },
    },
]

# The order plugins (if they're able to be shown on that particular page) will be displayed in. If not listed here, will be listed alphabetically after.
PLUGIN_ORDER = ['Activity','Status','OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory', 'DiskSpace', 'PendingAppleUpdates', 'Pending3rdPartyUpdates', 'PuppetStatus']

# Only show these plugins on the front page - some things only the admins should see.
LIMIT_PLUGIN_TO_FRONT_PAGE = []

# Hide these plugins from the front page
HIDE_PLUGIN_FROM_FRONT_PAGE = []

# Hide these plugins from the specified business units
HIDE_PLUGIN_FROM_BUSINESS_UNIT = {
    # 'Encryption':['1']
}

# Hide these plugins from the specified machine groups
HIDE_PLUGIN_FROM_MACHINE_GROUP = {
    # 'DiskSpace':['1']
}

# If you want to have a default machine group, define this to the key of
# that group.
#DEFAULT_MACHINE_GROUP_KEY = ''

# Facts which will have historical data kept in addition to the most
# recent instanct of that fact.
HISTORICAL_FACTS = [
    # 'memoryfree_mb',
]

# How long to keep historical facts around before pruning them.
HISTORICAL_DAYS = 180

EXCLUDED_FACTS = {
    'sshrsakey',
    'sshfp_rsa',
    'sshfp_dsa',
    'sshdsakey',
}

EXCLUDED_CONDITIONS = {
    # 'some_condition',
}
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'site_static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ppf%ls0f)mzkf#2dl-nbf^8f&=84py=y^u8^z-f559*d36y_@v'

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'server.middleware.AddToBU.AddToBU',
    'search.current_user.CurrentUserMiddleware',
)

LOGIN_URL='/login'
LOGIN_REDIRECT_URL='/'

ROOT_URLCONF = 'sal.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sal.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'sal',
    'server',
    'api',
    'catalog',
    'inventory',
    'licenses',
    'bootstrap3',
    'watson',
    'datatableview',
    'search',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'sal.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers':['file'],
            'propagate': True,
            'level':'ERROR',
        },
        'sal': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    }
}
BOOTSTRAP3 = {
    'set_placeholder': False,
}

if 'DYNO' in os.environ:
  # Parse database configuration from $DATABASE_URL
  import dj_database_url
  DATABASES['default'] =  dj_database_url.config()

  # Honor the 'X-Forwarded-Proto' header for request.is_secure()
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

  # Allow all host headers
  ALLOWED_HOSTS = ['*']

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 250
}
