from django.conf.urls.defaults import *

urlpatterns = patterns('server.views',
    #front page
    url(r'^$', 'index', name='home'),
    # BU Dashboard
    url(r'^dashboard/(?P<bu_id>.+)/', 'bu_dashboard', name='bu_dashboard'),
    # Group Dashboard
    url(r'^machinegroup/(?P<group_id>.+)/', 'group_dashboard', name='group_dashboard'),
    # #retrieve
    # url(r'^retrieve/(?P<request_id>.+)/', 'retrieve', name='retrieve'),
    # #approve
    # url(r'^approve/(?P<request_id>.+)/', 'approve', name='approve'),
    # checkin
    url(r'^checkin', 'checkin', name='checkin'),
    # New Business Unit
    url(r'^new-bu/', 'new_business_unit', name='new_business_unit'),
    # New Machine Group
    url(r'^new-machine-group/(?P<bu_id>.+)/', 'new_machine_group', name='new_machine_group'),
)
