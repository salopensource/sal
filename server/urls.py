from django.conf.urls import *

from server.settings_views import *
from server.non_ui_views import *
from server.views import *


urlpatterns = [
    # Primary views
    url(r'^$', index, name='home'),
    url(r'^dashboard/(?P<bu_id>.+)/', bu_dashboard, name='bu_dashboard'),
    url(r'^machinegroup/(?P<group_id>.+)/', group_dashboard, name='group_dashboard'),
    url(r'^machine_detail/facter/(?P<machine_id>.+)/',
        machine_detail_facter, name='machine_detail_facter'),
    url(r'^machine_detail/conditions/(?P<machine_id>.+)/',
        machine_detail_conditions, name='machine_detail_conditions'),
    url(r'^machine_detail/(?P<machine_id>.+)/', machine_detail, name='machine_detail'),

    # Checkin routes.
    url(r'^checkin/', checkin, name='checkin'),
    # TODO: Remove after sal-scripts have reasonably been updated to
    # not hit this endpoint.
    url(r'^installlog/hash/(?P<serial>.+)/$', install_log_hash, name='install_log_hash'),
    # TODO: Remove after sal-scripts have reasonably been updated to
    # not hit this endpoint.
    url(r'^installlog/submit/$', install_log_submit, name='install_log_submit'),
    url(r'^preflight/$', preflight, name='preflight'),
    url(r'^preflight-v2/get-script/(?P<plugin_name>.+)/(?P<script_name>.+)/$',
        preflight_v2_get_script, name='preflight_v2_get_script'),
    url(r'^preflight-v2/$', preflight_v2, name='preflight_v2'),

    # Plugin and calculated view routes.
    url(r'^load_plugin/(?P<plugin_name>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        plugin_load, name='load_plugin'),
    url(r'^report/(?P<plugin_name>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$', report_load,
        name='report_load'),

    url(r'^list/(?P<plugin_name>.+)/(?P<data>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        machine_list, name='machine_list'),
    # TODO: Deprecated along with old-school plugins.
    url(r'^list/(?P<plugin_name>.+)/(?P<data>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        machine_list, name='machine_list_id'),
    # TODO: Deprecated along with old-school plugins.
    url(r'^list/(?P<plugin_name>.+)/(?P<data>.+)/$', machine_list, name='machine_list_front'),

    url(r'^tableajax/(?P<plugin_name>.+)/(?P<data>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        tableajax, name='tableajax'),
    url(r'^csv/(?P<plugin_name>.+)/(?P<data>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        export_csv, name='export_csv'),
    # TODO: Deprecated along with old-school plugins.
    url(r'^csv/(?P<plugin_name>.+)/(?P<data>.+)/$', export_csv, name='export_csv_front'),
    # TODO: Deprecated along with old-school plugins.
    url(r'^csv/(?P<plugin_name>.+)/(?P<data>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        export_csv, name='export_csv_id'),

    # Business Unit routes.
    url(r'^new-bu/', new_business_unit, name='new_business_unit'),
    url(r'^business_unit/edit/(?P<bu_id>.+)/', edit_business_unit, name='edit_business_unit'),
    url(r'^business_unit/delete/(?P<bu_id>.+)/', delete_business_unit, name='delete_business_unit'),
    url(r'^business_unit/really/delete/(?P<bu_id>.+)/',
        really_delete_business_unit, name='really_delete_business_unit'),

    # Machine group routes.
    url(r'^machine_group/delete/(?P<group_id>.+)/', delete_machine_group,
        name='delete_machine_group'),
    url(r'^machine_group/really/delete/(?P<group_id>.+)/',
        really_delete_machine_group, name='really_delete_machine_group'),
    url(r'^new-machine-group/(?P<bu_id>.+)/', new_machine_group, name='new_machine_group'),
    url(r'^edit-machine-group/(?P<group_id>.+)/', edit_machine_group, name='edit_machine_group'),

    # Machine routes.
    url(r'^machine/delete/(?P<machine_id>.+)/', delete_machine, name='delete_machine'),
    url(r'^machine/new/(?P<group_id>.+)/', new_machine, name='new_machine'),

    # Settings routes

    # Users
    url(r'^settings/users/new/', new_user, name='new_user'),
    url(r'^settings/users/edit/(?P<user_id>.+)/', edit_user, name='edit_user'),
    url(r'^settings/users/makestaff/(?P<user_id>.+)/', user_add_staff, name='user_add_staff'),
    url(r'^settings/users/removestaff/(?P<user_id>.+)/',
        user_remove_staff, name='user_remove_staff'),
    url(r'^settings/users/delete/(?P<user_id>.+)/', delete_user, name='delete_user'),
    url(r'^settings/users/', manage_users, name='manage_users'),

    # API Keys
    url(r'^settings/api-keys/edit/(?P<key_id>.+)/', edit_api_key, name='edit_api_key'),
    url(r'^settings/api-keys/delete/(?P<key_id>.+)/', delete_api_key, name='delete_api_key'),
    url(r'^settings/api-keys/display/(?P<key_id>.+)/', display_api_key, name='display_api_key'),
    url(r'^settings/api-keys/new/', new_api_key, name='new_api_key'),
    url(r'^settings/api-keys/', api_keys, name='api_keys'),

    # Plugins
    url(r'^settings/plugins/plus/(?P<plugin_id>.+)/', plugin_plus, name='plugin_plus'),
    url(r'^settings/plugins/minus/(?P<plugin_id>.+)/', plugin_minus, name='plugin_minus'),
    url(r'^settings/plugins/disable/(?P<plugin_id>.+)/', plugin_disable, name='plugin_disable'),
    url(r'^settings/plugins/enable/(?P<plugin_name>.+)/', plugin_enable, name='plugin_enable'),

    # Reports
    url(r'^settings/plugins/reports/disable/(?P<plugin_id>.+)/',
        settings_report_disable, name='settings_report_disable'),
    url(r'^settings/plugins/reports/enable/(?P<plugin_name>.+)/',
        settings_report_enable, name='settings_report_enable'),
    url(r'^settings/plugins/reports/', settings_reports, name='settings_reports'),

    # Machine Detail Plugins
    url(r'^settings/plugins/machinedetail/plus/(?P<plugin_id>.+)/',
        machine_detail_plugin_plus, name='machine_detail_plugin_plus'),
    url(r'^settings/plugins/machinedetail/minus/(?P<plugin_id>.+)/',
        machine_detail_plugin_minus, name='machine_detail_plugin_minus'),
    url(r'^settings/plugins/machinedetail/disable/(?P<plugin_id>.+)/',
        machine_detail_plugin_disable, name='machine_detail_plugin_disable'),
    url(r'^settings/plugins/machinedetail/enable/(?P<plugin_name>.+)/',
        machine_detail_plugin_enable, name='machine_detail_plugin_enable'),
    url(r'^settings/plugins/machinedetail/', settings_machine_detail_plugins,
        name='settings_machine_detail_plugins'),

    url(r'^settings/plugins/', plugins_page, name='plugins_page'),

    # Configuration settings
    url(r'^settings/senddata/enable/', senddata_enable, name='senddata_enable'),
    url(r'^settings/senddata/disable/', senddata_disable, name='senddata_disable'),
    url(r'^settings/save_historical_days/', settings_historical_data,
        name='settings_historical_data'),
    url(r'^settings/', settings_page, name='settings_page'),
    url(r'^new_version/never/', new_version_never, name='new_version_never'),
    url(r'^new_version/week/', new_version_week, name='new_version_week'),
    url(r'^new_version/day/', new_version_day, name='new_version_day')
]
