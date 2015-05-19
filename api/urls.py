from django.conf.urls.defaults import *

urlpatterns = patterns('api.views',
    (r'^v1/machines/$', 'v1_machines'),
)
