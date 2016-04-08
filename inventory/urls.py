from django.conf.urls import url
from inventory import views

urlpatterns = [
    url(r'^submit/$', views.inventory_submit),
    # Hash
    url(r'^hash/(?P<serial>.+)/$', views.inventory_hash),
    # CSV Export (front page)
    # url(r'^csv/$', views.CSVExportView.as_view(), name='inventory_export_csv'),
    # Temporary CSV Export View
    url(r'^csv/(?P<group_type>.+)/'
        r'(?P<group_id>[0-9]+)/'
        r'(?P<application_id>[0-9]+)/$',
        views.CSVExportView.as_view(), name='inventory_export_csv'),
    # Application Detail View
    url(r'^application/'
        r'(?P<pk>[0-9]+)/'
        r'(?P<group_type>[a-zA-Z_-]+)/'
        r'(?P<group_id>[0-9]+)/$',
        views.ApplicationDetailView.as_view(),
        name="application_detail"),
    # Install List View
    url(r'^list/(?P<group_type>.+)/'
        r'(?P<group_id>[0-9]+)/'
        r'(?P<application_id>[0-9]+)/'
        r'(?P<field_type>[a-zA-Z]+)/{1}'
        r'(?P<field_value>.+)/$',
        views.InventoryListView.as_view(), name='inventory_list'),
    # GA Application List
    url(r'^(?P<group_type>.+)/'
        r'(?P<group_id>[0-9]+)/$', views.ApplicationListView.as_view(),
        name="application_list"),
]
