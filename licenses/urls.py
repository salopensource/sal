from django.urls import path

from licenses.views import *


urlpatterns = [
    path('', license_index, name='license_index'),
    path('available/<key>/', available),
    path('available/<key>/<item_name>/', available),
    path('usage/<key>/', usage),
    path('usage/<key>/<item_name>/', usage),
    path('edit/<license_id>/', edit_license, name='edit_license'),
    path('delete/<license_id>/', delete_license, name='delete_license'),
    path('new/', new_license, name='new_license'),
]
