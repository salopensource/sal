from django.urls import path

from server.settings_views import *
from server.non_ui_views import *
from server.views import *


urlpatterns = [
    # Primary views
    path('', index, name='home'),
    path('dashboard/<int:bu_id>/', bu_dashboard, name='bu_dashboard'),
    path('machinegroup/<int:group_id>/', group_dashboard, name='group_dashboard'),
    path('machine_detail/facts/<int:machine_id>/<management_source>/', machine_detail_facts,
         name='machine_detail_facts'),
    path('machine_detail/<int:machine_id>/', machine_detail, name='machine_detail'),

    # Checkin routes.
    path('checkin/', checkin, name='checkin'),
    path('report_broken_client/', report_broken_client, name='report_broken_client'),
    path('preflight-v2/get-script/<plugin_name>/<script_name>/', preflight_v2_get_script,
         name='preflight_v2_get_script'),
    path('preflight-v2/', preflight_v2, name='preflight_v2'),

    # Plugin and calculated view routes.
    path('load_plugin/<plugin_name>/<group_type>/<int:group_id>/', plugin_load, name='load_plugin'),
    path('report/<plugin_name>/<group_type>/<int:group_id>/', report_load, name='report_load'),

    path('list/<plugin_name>/<data>/<group_type>/<int:group_id>/', machine_list,
         name='machine_list'),

    path('tableajax/<plugin_name>/<data>/<group_type>/<int:group_id>/', tableajax,
         name='tableajax'),
    path('csv/<plugin_name>/<data>/<group_type>/<int:group_id>/', export_csv, name='export_csv'),

    # Business Unit routes.
    path('new-bu/', new_business_unit, name='new_business_unit'),
    path('business_unit/edit/<int:bu_id>/', edit_business_unit, name='edit_business_unit'),
    path('business_unit/delete/<int:bu_id>/', delete_business_unit, name='delete_business_unit'),
    path('business_unit/really/delete/<int:bu_id>/', really_delete_business_unit,
         name='really_delete_business_unit'),

    # Machine group routes.
    path('machine_group/delete/<int:group_id>/', delete_machine_group, name='delete_machine_group'),
    path('machine_group/really/delete/<int:group_id>/', really_delete_machine_group,
         name='really_delete_machine_group'),
    path('new-machine-group/<int:bu_id>/', new_machine_group, name='new_machine_group'),
    path('edit-machine-group/<int:group_id>/', edit_machine_group, name='edit_machine_group'),

    # Machine routes.
    path('machine/delete/<int:machine_id>/', delete_machine, name='delete_machine'),
    path('machine/new/<int:group_id>/', new_machine, name='new_machine'),

    # Settings routes

    # Users
    path('settings/users/new/', new_user, name='new_user'),
    path('settings/users/edit/<int:user_id>/', edit_user, name='edit_user'),
    path('settings/users/makestaff/<int:user_id>/', user_add_staff, name='user_add_staff'),
    path('settings/users/removestaff/<int:user_id>/', user_remove_staff, name='user_remove_staff'),
    path('settings/users/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('settings/users/', manage_users, name='manage_users'),

    # API Keys
    path('settings/api-keys/edit/<int:key_id>/', edit_api_key, name='edit_api_key'),
    path('settings/api-keys/delete/<int:key_id>/', delete_api_key, name='delete_api_key'),
    path('settings/api-keys/display/<int:key_id>/', display_api_key, name='display_api_key'),
    path('settings/api-keys/new/', new_api_key, name='new_api_key'),
    path('settings/api-keys/', api_keys, name='api_keys'),

    # Plugins
    path('settings/plugins/plus/<int:plugin_id>/', plugin_plus, name='plugin_plus'),
    path('settings/plugins/minus/<int:plugin_id>/', plugin_minus, name='plugin_minus'),
    path('settings/plugins/disable/<int:plugin_id>/', plugin_disable, name='plugin_disable'),
    path('settings/plugins/enable/<plugin_name>/', plugin_enable, name='plugin_enable'),

    # Reports
    path('settings/plugins/reports/disable/<int:plugin_id>/', settings_report_disable,
         name='settings_report_disable'),
    path('settings/plugins/reports/enable/<plugin_name>/', settings_report_enable,
         name='settings_report_enable'),
    path('settings/plugins/reports/', settings_reports, name='settings_reports'),

    # Machine Detail Plugins
    path('settings/plugins/machinedetail/plus/<int:plugin_id>/', machine_detail_plugin_plus,
         name='machine_detail_plugin_plus'),
    path('settings/plugins/machinedetail/minus/<int:plugin_id>/', machine_detail_plugin_minus,
         name='machine_detail_plugin_minus'),
    path('settings/plugins/machinedetail/disable/<int:plugin_id>/', machine_detail_plugin_disable,
         name='machine_detail_plugin_disable'),
    path('settings/plugins/machinedetail/enable/<plugin_name>/', machine_detail_plugin_enable,
         name='machine_detail_plugin_enable'),
    path('settings/plugins/machinedetail/', settings_machine_detail_plugins,
         name='settings_machine_detail_plugins'),

    path('settings/plugins/', plugins_page, name='plugins_page'),

    # Configuration settings
    path('settings/senddata/enable/', senddata_enable, name='senddata_enable'),
    path('settings/senddata/disable/', senddata_disable, name='senddata_disable'),
    path('settings/save_historical_days/', settings_historical_data,
         name='settings_historical_data'),
    path('settings/', settings_page, name='settings_page'),
    path('new_version/never/', new_version_never, name='new_version_never'),
    path('new_version/week/', new_version_week, name='new_version_week'),
    path('new_version/day/', new_version_day, name='new_version_day')
]
