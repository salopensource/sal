from django.urls import path

from . import views


urlpatterns = [
    path('submit/', views.submit_catalog),
    path('hash/', views.catalog_hash),
]
