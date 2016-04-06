from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Hash
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    # CSV Export (front page)
    url(r'^csv/$', views.export_csv, name='inventory_export_csv_front'),
    # CSV Export (id)
    url(r'^id_csv/(?P<page>.+)/(?P<theID>.+)/$', views.export_csv,
        name='inventory_export_csv_id'),
    # GA Application Detail
    url(r'^application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="application-detail"),
    # Business Unit Application Detail
    url(r'^business_unit/(?P<bu_id>[0-9]+)/application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="bu-application-detail"),
    # Machine Group Application Detail
    url(r'^machine_group/(?P<group_id>[0-9]+)/'
        r'application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="mg-application-detail"),
    # Machine Group Application Detail
    url(r'^machine/(?P<machine_id>[0-9]+)/'
        r'application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="machine-application-detail"),
    # GA Application List
    url(r'^$', views.ApplicationListView.as_view(),
        name="application-list"),
    # Business Unit Application List
    url(r'^business_unit/(?P<bu_id>.+)/$',
        views.BusinessUnitApplicationListView.as_view(),
        name="bu_inventory"),
    # Machine Group Application List
    url(r'^machine_group/(?P<group_id>.+)/$',
        views.MachineGroupApplicationListView.as_view(),
        name="machine_group_inventory"),
    # Machine Application List
    url(r'^machine/(?P<machine_id>.+)/$',
        views.MachineApplicationListView.as_view(), name="machine_inventory"),
    # Inventory List (front page)
    # url(r'^list/$', views.inventory_list, name='inventory_list_front'),
    # Inventory List (id)
    # url(r'^id_list/(?P<page>.+)/(?P<theID>.+)/$', views.inventory_list,
    #     name='inventory_list_id'),
]
