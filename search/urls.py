from django.conf.urls import url

from search import views


urlpatterns = [
    # Basic search
    url(r'^$', views.index, name="search_index"),
    # New Advanced search
    url(r'^new/$', views.new_search, name="search_new"),
    # New Advanced search
    url(r'^list/$', views.list_view, name="search_list"),
    # Build search
    url(r'^build_search/(?P<search_id>.+)/', views.build_search, name='search_build'),
    # New search group
    url(r'^new_search_group/(?P<search_id>.+)/', views.new_search_group, name='search_group_new'),

    # Delete search
    url(r'^delete_search/(?P<search_id>.+)/', views.delete_search, name='search_delete'),
    # Delete search group
    url(r'^delete_search_group/(?P<search_group_id>.+)/', views.delete_group,
        name='search_group_delete'),

    # Delete search row
    url(r'^delete_search_row/(?P<search_row_id>.+)/', views.delete_row, name='search_row_delete'),

    # Search group and or
    url(r'^and_or_group/(?P<search_group_id>.+)/', views.group_and_or, name='search_group_and_or'),
    # New search row
    url(r'^new_search_row/(?P<search_group_id>.+)/', views.new_search_row, name='search_row_new'),

    # Edit search row
    url(r'^edit_search_row/(?P<search_row_id>.+)/', views.edit_search_row, name='search_row_edit'),

    # Run advanced search
    url(r'^run_search/(?P<search_id>.+)/', views.run_search, name='search_run'),

    # Save advanced search
    url(r'^save_search/(?P<search_id>.+)/', views.save_search, name='search_save'),

    # Export CSV
    url(r'^csv/(?P<search_id>.+)/', views.export_csv, name='search_export_csv'),

    # Get field names
    url(r'^get_fields/(?P<model>.+)/', views.get_fields, name='search_get_fields'),]
