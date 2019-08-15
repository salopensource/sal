from django.urls import include, path

from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register('business_units', views.BusinessUnitViewSet)
router.register('facts', views.FactViewSet)
router.register('inventory', views.InventoryViewSet)
router.register('machine_groups', views.MachineGroupViewSet)
router.register('machines', views.MachineViewSet)
router.register('management_sources', views.ManagementSourceViewSet)
router.register('managed_items', views.ManagedItemViewSet)
router.register('managed_item_histories', views.ManagedItemHistoryViewSet)
router.register('messages', views.MessageViewSet)
router.register('plugin_script_rows', views.PluginScriptRowViewSet)
router.register('profiles', views.ProfileViewSet)
router.register('saved_searches', views.SavedSearchViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Include the docs separatly, so we can use the v2 URLs above to filter
# out the older API schema from the docs.
urlpatterns.append(
    path('docs/', include_docs_urls(
        title='Sal REST API', schema_url='/api/v2/', patterns=urlpatterns)))
