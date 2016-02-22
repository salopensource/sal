from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Inventory List (front page)
    url(r'^list/$', views.inventory_list, name='inventory_list_front'),
    # Inventory List (id)
    url(r'^id_list/(?P<page>.+)/(?P<theID>.+)/$', views.inventory_list,
        name='inventory_list_id'),
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    url(r'^business_unit/(?P<bu_id>.+)/$', views.bu_inventory),
    url(r'^machine_group/(?P<group_id>.+)/$', views.machine_group_inventory),
    url(r'^machine/(?P<machine_id>.+)/$', views.machine_inventory),
    # CSV Export (front page)
    url(r'^csv/$', views.export_csv, name='inventory_export_csv_front'),
    # CSV Export (id)
    url(r'^id_csv/(?P<page>.+)/(?P<theID>.+)/$', views.export_csv,
        name='inventory_export_csv_id'),
    url(r'^$', login_required(views.ApplicationView.as_view()),
        name="application-list"),
    url(r'^application/(?P<pk>[0-9]+)/$',
        login_required(views.ApplicationDetailView.as_view()),
        name="application-detail"),
]
