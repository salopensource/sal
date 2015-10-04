import os
DEBUG = False
TEMPLATE_DEBUG = DEBUG
APPEND_SLASH=True
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir))
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

AUTH_PROFILE_MODULE = "sal.UserProfile"
DISPLAY_NAME = 'Sal'
MANAGERS = ADMINS

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

PLUGIN_DIR = os.path.join(PROJECT_DIR, 'plugins')

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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "sal.context_processors.display_name",
    "sal.context_processors.config_installed",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

LOGIN_URL='/login/'
LOGIN_REDIRECT_URL='/'

ROOT_URLCONF = 'sal.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sal.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),
    os.path.join(PROJECT_DIR, 'server', 'plugins'),
    PLUGIN_DIR,
)


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
    'inventory',
    'licenses',
    'bootstrap3',
    'watson',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
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
