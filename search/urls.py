from django.urls import path

from search import views


urlpatterns = [
    path('', views.index, name="search_index"),
    path('new/', views.new_search, name="search_new"),
    path('list/', views.list_view, name="search_list"),
    path('build_search/<int:search_id>/', views.build_search, name='search_build'),
    path('new_search_group/<int:search_id>/', views.new_search_group, name='search_group_new'),
    path('delete_search/<int:search_id>/', views.delete_search, name='search_delete'),
    path('delete_search_group/<int:search_group_id>/', views.delete_group,
         name='search_group_delete'),
    path('delete_search_row/<int:search_row_id>/', views.delete_row, name='search_row_delete'),
    path('and_or_group/<int:search_group_id>/', views.group_and_or, name='search_group_and_or'),
    path('new_search_row/<int:search_group_id>/', views.new_search_row, name='search_row_new'),
    path('edit_search_row/<int:search_row_id>/', views.edit_search_row, name='search_row_edit'),
    path('run_search/<int:search_id>/', views.run_search, name='search_run'),
    path('save_search/<int:search_id>/', views.save_search, name='search_save'),
    path('csv/<int:search_id>/', views.export_csv, name='search_export_csv'),
    path('get_fields/<model>/', views.get_fields, name='search_get_fields'), ]
