from django.conf.urls import url
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Hash
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    # Application Detail View
    url(
        r'^application/(?P<pk>[0-9]+)/$',
        views.ApplicationDetailView.as_view(), name="application_detail"),
    # Install List View
    url(
        r'^list/(?P<application_id>[0-9]+)/$',
        views.InventoryListView.as_view(), name='inventory_list'),
    # CSV Export View
    url(
        r'^csv_export/$', views.CSVExportView.as_view(), name='csv_export'),
    # GA Application List
    url(r'^(?P<group_type>.+)/(?P<group_id>[0-9]+)/$', views.ApplicationListView.as_view(),
        name="application_list"),
]
