from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from . import views


router = DefaultRouter()
router.register("business_units", views.BusinessUnitViewSet)
router.register("facts", views.FactViewSet)
router.register("inventory", views.InventoryViewSet)
router.register("machine_groups", views.MachineGroupViewSet)
router.register("machines", views.MachineViewSet)
router.register("management_sources", views.ManagementSourceViewSet)
router.register("managed_items", views.ManagedItemViewSet)
router.register("managed_item_histories", views.ManagedItemHistoryViewSet)
router.register("messages", views.MessageViewSet)
router.register("plugin_script_rows", views.PluginScriptRowViewSet)
router.register("profiles", views.ProfileViewSet)
router.register("saved_searches", views.SavedSearchViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "openapi",
        get_schema_view(title="Sal API", description="API for Sal", version="2.0.0"),
        name="openapi-schema",
    ),
]

# Include the docs separatly, so we can use the v2 URLs above to filter
# out the older API schema from the docs.
urlpatterns.append(
    path(
        "docs/",
        TemplateView.as_view(
            template_name="redoc.html", extra_context={"schema_url": "openapi-schema"}
        ),
        name="redoc",
    ),
)
