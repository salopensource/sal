###############
INSTALLED_APPS+= ('axes',)
MIDDLEWARE_CLASSES+=('axes.middleware.FailedLoginMiddleware',)
# Max number of login attemts within the ``AXES_COOLOFF_TIME``
AXES_LOGIN_FAILURE_LIMIT = BRUTE_LIMIT
AXES_COOLOFF_TIME=BRUTE_COOLOFF