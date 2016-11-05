from django.conf.urls import url
from api import views

urlpatterns = [
    url(r'^machines/(?P<serial>.+)/inventory/$', views.machine_inventory),
    url(r'^machines/(?P<serial>.+)/$', views.machine_detail),
    url(r'^machines/(?P<serial>.+)/full/$', views.machine_full_detail),
    url(r'^machines/$', views.machine_list),
    url(r'^facts/(?P<serial>.+)/$', views.facts),
    url(r'^conditions/(?P<serial>.+)/$', views.conditions),
    url(r'^pending_apple_updates/(?P<serial>.+)/$', views.pending_apple_updates),
    url(r'^pending_updates/(?P<serial>.+)/$', views.pending_updates),
    url(r'^business_units/(?P<pk>.+)/$', views.business_unit),
    url(r'^business_units/$', views.business_unit_list),
    url(r'^machine_groups/(?P<pk>.+)/$', views.machine_group),
    url(r'^machine_groups/$', views.machine_group_list),
]
