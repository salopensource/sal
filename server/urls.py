from django.conf.urls import *

from server.settings_views import *
from server.non_ui_views import *
from server.views import *


urlpatterns = [
    # front page
    url(r'^$', index, name='home'),
    # checkin
    url(r'^checkin/', checkin, name='checkin'),
    # Install log hash
    url(r'^installlog/hash/(?P<serial>.+)/$', install_log_hash, name='install_log_hash'),
    # Install log submit
    url(r'^installlog/submit/$', install_log_submit, name='install_log_submit'),
    # preflight
    url(r'^preflight/$', preflight, name='preflight'),
    # preflight get script v2
    url(r'^preflight-v2/get-script/(?P<pluginName>.+)/(?P<scriptName>.+)/$',
        preflight_v2_get_script, name='preflight_v2_get_script'),
    # preflight v2
    url(r'^preflight-v2/$', preflight_v2, name='preflight_v2'),
    # Search
    # url(r'^search/', search, name='search'),
    # BU Dashboard
    url(r'^dashboard/(?P<bu_id>.+)/', bu_dashboard, name='bu_dashboard'),

    url(r'^load_plugin/(?P<plugin_name>.+)/(?P<group_type>.+)/(?P<group_id>.+)/$',
        plugin_load, name='load_plugin'),

    # tableajax (front page)
    url(r'^tableajax/(?P<pluginName>.+)/(?P<data>.+)/$', tableajax, name='tableajax_front'),
    # tableajax (id)
    url(r'^id_tableajax/(?P<pluginName>.+)/(?P<data>.+)/(?P<page>.+)/(?P<theID>.+)/$',
        tableajax, name='tableajax_id'),
    # reporload (front page)
    url(r'^report/(?P<pluginName>.+)/$', report_load, name='report_load_front'),
    # report (id)
    url(r'^id_report/(?P<pluginName>.+)/(?P<page>.+)/(?P<theID>.+)/$', report_load,
        name='report_load_id'),
    url(r'^list/(?P<plugin_name>.+)/(?P<data>.+)/(?P<page>.+)/(?P<instance_id>.+)/$',
        machine_list, name='machine_list_id'),
    url(r'^list/(?P<plugin_name>.+)/(?P<data>.+)/$', machine_list, name='machine_list_front'),

    # # CSV Export (front page)
    url(r'^csv/(?P<pluginName>.+)/(?P<data>.+)/$', export_csv, name='export_csv_front'),
    # CSS Ecport (id)
    url(r'^id_csv/(?P<pluginName>.+)/(?P<data>.+)/(?P<page>.+)/(?P<theID>.+)/$',
        export_csv, name='export_csv_id'),

    # Group Dashboard
    url(r'^machinegroup/(?P<group_id>.+)/', group_dashboard, name='group_dashboard'),
    # Machine detail facter
    url(r'^machine_detail/facter/(?P<machine_id>.+)/',
        machine_detail_facter, name='machine_detail_facter'),
    # Machine detail facter
    url(r'^machine_detail/conditions/(?P<machine_id>.+)/',
        machine_detail_conditions, name='machine_detail_conditions'),
    # Machine detail
    url(r'^machine_detail/(?P<machine_id>.+)/', machine_detail, name='machine_detail'),
    # Delete Machine
    url(r'^machine/delete/(?P<machine_id>.+)/', delete_machine, name='delete_machine'),
    # New Machine
    url(r'^machine/new/(?P<group_id>.+)/', new_machine, name='new_machine'),
    # New Business Unit
    url(r'^new-bu/', new_business_unit, name='new_business_unit'),
    # Edit Business Unit
    url(r'^business_unit/edit/(?P<bu_id>.+)/', edit_business_unit, name='edit_business_unit'),
    # Delete Business Unit
    url(r'^business_unit/delete/(?P<bu_id>.+)/', delete_business_unit, name='delete_business_unit'),
    # Really Delete Business Unit
    url(r'^business_unit/really/delete/(?P<bu_id>.+)/',
        really_delete_business_unit, name='really_delete_business_unit'),
    # Delete Machine Group
    url(r'^machine_group/delete/(?P<group_id>.+)/', delete_machine_group,
        name='delete_machine_group'),
    # Really Delete Machine Group
    url(r'^machine_group/really/delete/(?P<group_id>.+)/',
        really_delete_machine_group, name='really_delete_machine_group'),
    # New Machine Group
    url(r'^new-machine-group/(?P<bu_id>.+)/', new_machine_group, name='new_machine_group'),
    # Edit Machine Group
    url(r'^edit-machine-group/(?P<group_id>.+)/', edit_machine_group, name='edit_machine_group'),
    # New User
    url(r'^settings/users/new/', new_user, name='new_user'),
    # Enable sending data
    url(r'^settings/senddata/enable/', senddata_enable, name='senddata_enable'),
    # disable sending data
    url(r'^settings/senddata/disable/', senddata_disable, name='senddata_disable'),
    # Edit User
    url(r'^settings/users/edit/(?P<user_id>.+)/', edit_user, name='edit_user'),
    # Make User Staff
    url(r'^settings/users/makestaff/(?P<user_id>.+)/', user_add_staff, name='user_add_staff'),
    # Remove User Staff
    url(r'^settings/users/removestaff/(?P<user_id>.+)/',
        user_remove_staff, name='user_remove_staff'),
    # Delete User Staff
    url(r'^settings/users/delete/(?P<user_id>.+)/', delete_user, name='delete_user'),
    # Manage Users
    url(r'^settings/users/', manage_users, name='manage_users'),
    # Edit API Key
    url(r'^settings/api-keys/edit/(?P<key_id>.+)/', edit_api_key, name='edit_api_key'),
    # Delete API Key
    url(r'^settings/api-keys/delete/(?P<key_id>.+)/', delete_api_key, name='delete_api_key'),
    # Display API Key
    url(r'^settings/api-keys/display/(?P<key_id>.+)/', display_api_key, name='display_api_key'),
    # New API Key
    url(r'^settings/api-keys/new/', new_api_key, name='new_api_key'),
    # Manage API Keys
    url(r'^settings/api-keys/', api_keys, name='api_keys'),
    # Disable Report
    url(r'^settings/plugins/reports/disable/(?P<plugin_id>.+)/',
        settings_report_disable, name='settings_report_disable'),
    # Enable Report
    url(r'^settings/plugins/reports/enable/(?P<plugin_name>.+)/',
        settings_report_enable, name='settings_report_enable'),
    # Manage Reports
    url(r'^settings/plugins/reports/', settings_reports, name='settings_reports'),
    # Plus Machine Detail Plugin
    url(r'^settings/plugins/machinedetail/plus/(?P<plugin_id>.+)/',
        machine_detail_plugin_plus, name='machine_detail_plugin_plus'),
    # Minus Machine Detail Plugin
    url(r'^settings/plugins/machinedetail/minus/(?P<plugin_id>.+)/',
        machine_detail_plugin_minus, name='machine_detail_plugin_minus'),
    # Disable Machine Detail Plugin
    url(r'^settings/plugins/machinedetail/disable/(?P<plugin_id>.+)/',
        machine_detail_plugin_disable, name='machine_detail_plugin_disable'),
    # Enable Machine Detail Plugin
    url(r'^settings/plugins/machinedetail/enable/(?P<plugin_name>.+)/',
        machine_detail_plugin_enable, name='machine_detail_plugin_enable'),
    # Manage Machine Detail Plugins
    url(r'^settings/plugins/machinedetail/', settings_machine_detail_plugins,
        name='settings_machine_detail_plugins'),
    # Plus Plugin
    url(r'^settings/plugins/plus/(?P<plugin_id>.+)/', plugin_plus, name='plugin_plus'),
    # Minus Plugin
    url(r'^settings/plugins/minus/(?P<plugin_id>.+)/', plugin_minus, name='plugin_minus'),
    # Disable Plugin
    url(r'^settings/plugins/disable/(?P<plugin_id>.+)/', plugin_disable, name='plugin_disable'),
    # Enable Plugin
    url(r'^settings/plugins/enable/(?P<plugin_name>.+)/', plugin_enable, name='plugin_enable'),
    # Manage Plugins
    url(r'^settings/plugins/', plugins_page, name='plugins_page'),
    # Save Historical days
    url(
        r'^settings/save_historical_days/',
        settings_historical_data,
        name='settings_historical_data'
    ),
    # Settings
    url(r'^settings/', settings_page, name='settings_page'),
    url(r'^new_version/never/', new_version_never, name='new_version_never'),
    url(r'^new_version/week/', new_version_week, name='new_version_week'),
    url(r'^new_version/day/', new_version_day, name='new_version_day')
]
