from django.urls import path, re_path

from . import views


urlpatterns = [
    re_path(r'^[^v2].*/$', views.deprecation_view),
    path(r'', views.deprecation_view),
]
