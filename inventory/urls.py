from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Inventory List (front page)
    # url(r'^list/$', views.inventory_list, name='inventory_list_front'),
    # Inventory List (id)
    # url(r'^id_list/(?P<page>.+)/(?P<theID>.+)/$', views.inventory_list,
    #     name='inventory_list_id'),
    # Hash
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    # Machine Group Application Detail
    url(r'^machine_group/(?P<machine_group>[0-9]+)/'
        r'application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="mg-application-detail"),
    # Business Unit Application Detail
    url(r'^business_unit/(?P<bu_id>[0-9]+)/application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="bu-application-detail"),
    # Business Unit Application Inventory
    url(r'^business_unit/(?P<bu_id>.+)/$',
        views.BusinessUnitApplicationView.as_view(),
        name="bu_inventory"),
    # Machine Group Application Inventory
    url(r'^machine_group/(?P<group_id>.+)/$',
        views.MachineGroupApplicationView.as_view(),
        name="machine_group_inventory"),
    # Machine Application Inventory
    url(r'^machine/(?P<machine_id>.+)/$',
        views.MachineApplicationView.as_view(), name="machine_inventory"),
    # CSV Export (front page)
    url(r'^csv/$', views.export_csv, name='inventory_export_csv_front'),
    # CSV Export (id)
    url(r'^id_csv/(?P<page>.+)/(?P<theID>.+)/$', views.export_csv,
        name='inventory_export_csv_id'),
    # GA Application Inventory
    url(r'^$', views.ApplicationView.as_view(),
        name="application-list"),
    # GA Application Detail
    url(r'^application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="application-detail"),
]
