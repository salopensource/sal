from django.conf.urls import url
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    url(r'^machines/(?P<serial>.+)/inventory/$', views.MachineInventory.as_view()),
    url(r'^machines/(?P<serial>.+)/full/$', views.MachineFullDetail.as_view()),
    url(r'^machines/(?P<serial>.+)/$', views.MachineDetail.as_view()),
    url(r'^machines/$', views.MachineList.as_view()),
    url(r'^machines_full/$', views.MachineListFullDetail.as_view()),
    url(r'^inventory/$', views.AllInventory.as_view()),
    url(r'^facts/(?P<serial>.+)/$', views.FactsMachine.as_view()),
    url(r'^facts/$', views.Facts.as_view()),
    url(r'^conditions/(?P<serial>.+)/$', views.ConditionsMachine.as_view()),
    url(r'^conditions/$', views.Conditions.as_view()),
    url(r'^pending_apple_updates/(?P<serial>.+)/$', views.PendingAppleUpdates.as_view()),
    url(r'^business_units/(?P<pk>.+)/$', views.BusinessUnitView.as_view()),
    url(r'^business_units/$', views.BusinessUnitList.as_view()),
    url(r'^machine_groups/(?P<pk>.+)/$', views.MachineGroupView.as_view()),
    url(r'^machine_groups/$', views.MachineGroupList.as_view()),
    url(r'^plugin_script_submissions/(?P<serial>.+)/$',
        views.PluginScriptSubmissionMachine.as_view()),
    url(r'^plugin_script_submissions/$', views.PluginScriptSubmissionList.as_view()),
    url(r'^plugin_script_rows/(?P<serial>.+)/$', views.PluginScriptRowMachine.as_view()),
    url(r'^search/(?P<pk>.+)$', views.SearchID.as_view()),
    url(r'^search/$', views.BasicSearch.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
