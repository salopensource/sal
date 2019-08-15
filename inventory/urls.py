from django.urls import path

from inventory import views


urlpatterns = [
    path('submit/', views.inventory_submit),
    path('hash/<serial>/', views.inventory_hash),
    path('application/<group_type>/<int:group_id>/<int:pk>/', views.ApplicationDetailView.as_view(),
         name="application_detail"),
    path('list/<group_type>/<int:group_id>/<int:application_id>/',
         views.InventoryListView.as_view(), name='inventory_list'),
    path('csv_export/<group_type>/<int:group_id>/', views.CSVExportView.as_view(),
         name='csv_export'),
    path('<group_type>/<int:group_id>/', views.ApplicationListView.as_view(),
         name="application_list"),
]
