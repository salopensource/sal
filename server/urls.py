from django.conf.urls import *

urlpatterns = patterns('server.views',
    #front page
    url(r'^$', 'index', name='home'),
    # BU Dashboard
    url(r'^dashboard/(?P<bu_id>.+)/', 'bu_dashboard', name='bu_dashboard'),
    # Overview List (Group)
    #url(r'^machinegroup/overview/(?P<group_id>.+)/(?P<req_type>.+)/(?P<data>.+)/$', 'overview_list_group', name='overview_list_group'),
    # Overview List (Group)
    #url(r'^bu/overview/(?P<req_type>.+)/(?P<data>.+)/(?P<bu_id>.+)/$', 'overview_list_all', name='overview_list_bu'),
    # Overview List (All)
    #url(r'^overview/(?P<req_type>.+)/(?P<data>.+)/$', 'overview_list_all', name='overview_list_all'),
    # Machine List (front page)
    url(r'^list/(?P<pluginName>.+)/(?P<data>.+)/$', 'machine_list', name='machine_list_front'),
    
    # Machine List (id)
    url(r'^id_list/(?P<pluginName>.+)/(?P<data>.+)/(?P<page>.+)/(?P<theID>.+)/$', 'machine_list', name='machine_list_id'),
    # Group Dashboard
    url(r'^machinegroup/(?P<group_id>.+)/', 'group_dashboard', name='group_dashboard'),
    # Machine detail
    url(r'^machine_detail/(?P<machine_id>.+)/', 'machine_detail', name='machine_detail'),
    # checkin
    url(r'^checkin', 'checkin', name='checkin'),
    # New Business Unit
    url(r'^new-bu/', 'new_business_unit', name='new_business_unit'),
    # New Machine Group
    url(r'^new-machine-group/(?P<bu_id>.+)/', 'new_machine_group', name='new_machine_group'),
)
