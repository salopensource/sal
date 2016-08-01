from django.conf.urls import url
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Inventory List (front page)
    url(r'^list/$', views.inventory_list, name='inventory_list_front'),
    # Inventory List (id)
    url(r'^id_list/(?P<page>.+)/(?P<theID>.+)/$', views.inventory_list, name='inventory_list_id'),
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    url(r'^business_unit/(?P<bu_id>.+)/$', views.bu_inventory),
    url(r'^machine_group/(?P<group_id>.+)/$', views.machine_group_inventory),
    url(r'^machine/(?P<machine_id>.+)/$', views.machine_inventory),
    # CSV Export (front page)
    url(r'^csv/$', views.export_csv, name='inventory_export_csv_front'),
    # CSS Ecport (id)
    url(r'^id_csv/(?P<page>.+)/(?P<theID>.+)/$', views.export_csv, name='inventory_export_csv_id'),
    url(r'^$', views.index, name='inventory_index'),
]
