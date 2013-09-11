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
    # #manage
    # url(r'^manage-requests/', 'managerequests', name='managerequests'),
)
