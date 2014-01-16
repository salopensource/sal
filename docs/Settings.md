# Settings.py

By modifying ``sal/settings.py`` you can customise how plugins and data is displayed in Sal. If you are upgrading from a previous version of Sal, refer to this document to see how your ``settings.py`` file should be changed to take advantage of any new features.

``` python
# The order plugins (if they're able to be shown on that particular page) will be displayed in. If not listed here, will be listed alphabetically after.
PLUGIN_ORDER = ['Activity','Status','OperatingSystem','Uptime', 'Memory']

# Only show these plugins on the front page - some things only the admins should see.
LIMIT_PLUGIN_TO_FRONT_PAGE = []

# Hide these plugins from the front page
HIDE_PLUGIN_FROM_FRONT_PAGE = ['DiskSpace']

# Hide these plugins from the specified business units
HIDE_PLUGIN_FROM_BUSINESS_UNIT = {
    'Encryption':['1']
}

# Hide these plugins from the specified machine groups
HIDE_PLUGIN_FROM_MACHINE_GROUP = {
    'DiskSpace':['1']
}
```