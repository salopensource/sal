from django.conf.urls import *
from licenses.views import *
urlpatterns = [
    url(r'^$', license_index, name='license_index'),
    url(r'^available/(?P<key>.+)', available),
    url(r'^available/(?P<key>.+)(?P<item_name>[^/]+)$', available),
    url(r'^usage/$', usage),
    url(r'^usage/(?P<item_name>[^/]+)$', usage),
    # Edit License
    url(r'^edit/(?P<license_id>.+)/', edit_license, name='edit_license'),
    # Delete License
    url(r'^delete/(?P<license_id>.+)/', delete_license, name='delete_license'),
    # New License
    url(r'^new/$', new_license, name='new_license'),
]
