from django.conf.urls import include, url

from rest_framework.documentation import include_docs_urls
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from api import views


# TODO: Make this a DefaultRouter when finished moving URLs.
router = SimpleRouter()
router.register(r'business_units', views.BusinessUnitViewSet)
router.register(r'conditions', views.ConditionViewSet)
router.register(r'facts', views.FactViewSet)
router.register(r'inventory', views.InventoryViewSet)
router.register(r'machine_groups', views.MachineGroupViewSet)
router.register(r'machines', views.MachineViewSet)
router.register(r'pending_apple_updates', views.PendingAppleUpdatesViewSet)
router.register(r'pending_updates', views.PendingUpdatesViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^plugin_script_submissions/(?P<serial>.+)/$',
        views.PluginScriptSubmissionMachine.as_view()),
    url(r'^plugin_script_submissions/$',
        views.PluginScriptSubmissionList.as_view()),
    url(r'^plugin_script_rows/(?P<serial>.+)/$',
        views.PluginScriptRowMachine.as_view()),
    url(r'^search/(?P<pk>.+)$', views.SearchID.as_view()),
    url(r'^search/$', views.BasicSearch.as_view()),
    url(r'^docs/', include_docs_urls(title='Sal REST API')),
    url(r'^api-auth/', include(
        'rest_framework.urls', namespace='rest_framework')),
]

urlpatterns = format_suffix_patterns(urlpatterns)
