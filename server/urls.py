from django.conf.urls import *

urlpatterns = patterns('server.views',
    #front page
    url(r'^$', 'index', name='home'),
    # checkin
    url(r'^checkin/', 'checkin', name='checkin'),
    # preflight
    url(r'^preflight/', 'preflight', name='preflight'),
    # Search
    url(r'^search/', 'search', name='search'),
    # BU Dashboard
    url(r'^dashboard/(?P<bu_id>.+)/', 'bu_dashboard', name='bu_dashboard'),
    # pluginload (front page)
    url(r'^pluginload/(?P<pluginName>.+)/$', 'plugin_load', name='plugin_load_front'),
    # pluginload (id)
    url(r'^id_pluginload/(?P<pluginName>.+)/(?P<page>.+)/(?P<theID>.+)/$', 'plugin_load', name='plugin_load_id'),
    # Machine List (front page)
    url(r'^list/(?P<pluginName>.+)/(?P<data>.+)/$', 'machine_list', name='machine_list_front'),
    # Machine List (id)
    url(r'^id_list/(?P<pluginName>.+)/(?P<data>.+)/(?P<page>.+)/(?P<theID>.+)/$', 'machine_list', name='machine_list_id'),
    # CSV Export (front page)
    url(r'^csv/(?P<pluginName>.+)/(?P<data>.+)/$', 'export_csv', name='export_csv_front'),
    # CSS Ecport (id)
    url(r'^id_csv/(?P<pluginName>.+)/(?P<data>.+)/(?P<page>.+)/(?P<theID>.+)/$', 'export_csv', name='export_csv_id'),
    # Group Dashboard
    url(r'^machinegroup/(?P<group_id>.+)/', 'group_dashboard', name='group_dashboard'),
    # Machine detail
    url(r'^machine_detail/(?P<machine_id>.+)/', 'machine_detail', name='machine_detail'),
    # Delete Machine
    url(r'^machine/delete/(?P<machine_id>.+)/', 'delete_machine', name='delete_machine'),
    # New Machine
    url(r'^machine/new/(?P<group_id>.+)/', 'new_machine', name='new_machine'),

    # New Business Unit
    url(r'^new-bu/', 'new_business_unit', name='new_business_unit'),
    # Edit Business Unit
    url(r'^business_unit/edit/(?P<bu_id>.+)/', 'edit_business_unit', name='edit_business_unit'),
    # Delete Business Unit
    url(r'^business_unit/delete/(?P<bu_id>.+)/', 'delete_business_unit', name='delete_business_unit'),
    # Really Delete Business Unit
    url(r'^business_unit/really/delete/(?P<bu_id>.+)/', 'really_delete_business_unit', name='really_delete_business_unit'),
    # New Machine Group
    url(r'^new-machine-group/(?P<bu_id>.+)/', 'new_machine_group', name='new_machine_group'),
    # Edit Machine Group
    url(r'^edit-machine-group/(?P<group_id>.+)/', 'edit_machine_group', name='edit_machine_group'),
    # New User
    url(r'^settings/users/new/', 'new_user', name='new_user'),

    # Edit User
    url(r'^settings/users/edit/(?P<user_id>.+)/', 'edit_user', name='edit_user'),
    # Make User Staff
    url(r'^settings/users/makestaff/(?P<user_id>.+)/', 'user_add_staff', name='user_add_staff'),
    # Remove User Staff
    url(r'^settings/users/removestaff/(?P<user_id>.+)/', 'user_remove_staff', name='user_remove_staff'),

    # Delete User Staff
    url(r'^settings/users/delete/(?P<user_id>.+)/', 'delete_user', name='delete_user'),
    # unlock user
    url(r'^settings/users/unlock/', 'brute_unlock', name='brute_unlock'),
    # Manage Users
    url(r'^settings/users/', 'manage_users', name='manage_users'),

    #Edit API Key
    url(r'^settings/api-keys/edit/(?P<key_id>.+)/', 'edit_api_key', name='edit_api_key'),
    #Delete API Key
    url(r'^settings/api-keys/delete/(?P<key_id>.+)/', 'delete_api_key', name='delete_api_key'),
    #Display API Key
    url(r'^settings/api-keys/display/(?P<key_id>.+)/', 'display_api_key', name='display_api_key'),
    # New API Key
    url(r'^settings/api-keys/new/', 'new_api_key', name='new_api_key'),
    # Manage API Keys
    url(r'^settings/api-keys/', 'api_keys', name='api_keys'),
    # Plus Plugin
    url(r'^settings/plugins/plus/(?P<plugin_id>.+)/', 'plugin_plus', name='plugin_plus'),
    # Minus Plugin
    url(r'^settings/plugins/minus/(?P<plugin_id>.+)/', 'plugin_minus', name='plugin_minus'),
    # Disable Plugin
    url(r'^settings/plugins/disable/(?P<plugin_id>.+)/', 'plugin_disable', name='plugin_disable'),
    # Enable Plugin
    url(r'^settings/plugins/enable/(?P<plugin_name>.+)/', 'plugin_enable', name='plugin_enable'),
    # Manage Plugins
    url(r'^settings/plugins/', 'plugins_page', name='plugins_page'),
    # Save Historical days
    url(r'^settings/save_historical_days/', 'settings_historical_data', name='settings_historical_data'),
    # Settings
    url(r'^settings/', 'settings_page', name='settings_page')
)
