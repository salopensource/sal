from django.conf.urls import url
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    url(r'^business_unit/(?P<bu_id>.+)/$', views.bu_inventory),
    url(r'^machine_group/(?P<group_id>.+)/$', views.machine_group_inventory),
    url(r'^$', views.index),
]
