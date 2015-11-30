from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^submit/$', views.submit_catalog),
    url(r'^hash/$', views.catalog_hash),
]
