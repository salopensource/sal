from django.conf.urls import include, url

from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'business_units', views.BusinessUnitViewSet)
router.register(r'conditions', views.ConditionViewSet)
router.register(r'facts', views.FactViewSet)
router.register(r'inventory', views.InventoryViewSet)
router.register(r'machine_groups', views.MachineGroupViewSet)
router.register(r'machines', views.MachineViewSet)
router.register(r'pending_apple_updates', views.PendingAppleUpdatesViewSet)
router.register(r'pending_updates', views.PendingUpdatesViewSet)
router.register(r'plugin_script_rows', views.PluginScriptRowViewSet)
router.register(r'saved_searches', views.SavedSearchViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include(
        'rest_framework.urls', namespace='rest_framework')),
]

# Include the docs separatly, so we can use the v2 URLs above to filter
# out the older API schema from the docs.
urlpatterns.append(
    url(r'^docs/', include_docs_urls(
        title='Sal REST API', schema_url='/api/v2/', patterns=urlpatterns)))
