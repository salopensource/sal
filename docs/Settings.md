# Settings.py

By modifying ``sal/settings.py`` you can customise how plugins and data is displayed in Sal. If you are upgrading from a previous version of Sal, refer to this document to see how your ``settings.py`` file should be changed to take advantage of any new features.

## PLUGIN_ORDER

This is a list of plugin names. They will be displayed in the order they are entered in this list. If they are not in this this, they will be displayed alphabetically after the items in the ``PLUGIN_ORDER`` list.

``` python
PLUGIN_ORDER = ['Activity','Status','OperatingSystem','Uptime', 'Memory']
```

To have all plugins displaying alphabetically, with none in any particular order:

```python
PLUGIN_ORDER = []
```

## LIMIT_PLUGIN_TO_FRONT_PAGE

These plugins will only be shown on the front page. They will not appear anywhere else.

```python
LIMIT_PLUGIN_TO_FRONT_PAGE = ['Uptime', 'Memory']
```

## HIDE_PLUGIN_FROM_FRONT_PAGE

Once again, a list of plugin names. These will not be shown on the front page.

```python
HIDE_PLUGIN_FROM_FRONT_PAGE = ['DiskSpace']
```

## HIDE_PLUGIN_FROM_BUSINESS_UNIT

Specify which Business Unit IDs should be hidden from which plugins. The data should be a dictionary containing lists. The Business Unit ID will be shown in the URL when on that particular Business Unit's page.

```python
HIDE_PLUGIN_FROM_BUSINESS_UNIT = {
    'Encryption':['1','2','4'],
    'DiskSpace':['5','7','9']
}
```

## HIDE_PLUGIN_FROM_MACHINE_GROUP

Works exactly the same as ``HIDE_PLUGIN_FROM_BUSINESS_UNIT`` (although you are specifying the Machine Group ID, obviously!),

```python
HIDE_PLUGIN_FROM_MACHINE_GROUP = {
    'DiskSpace':['1'],
    'Uptime':['2','8']
}
```