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

## EXCLUDED_FACTS

These Facts won't be displayed on the Machine Information page. This won't effect any plugins that rely on the Fact.

```python
EXCLUDED_FACTS = {
    'sshrsakey',
    'sshfp_rsa',
    'sshfp_dsa',
    'sshdsakey',
}
```

## EXCLUDED_CONDTIONS

The same as ``EXCLUDED_FACTS``, but will hide Munki Conditions instead.

```python
EXCLUDED_CONDTIONS = {
    'ipv4_address',
}
```

## DEFAULT_MACHINE_GROUP_KEY

By default, all machine submissions must include a machine group key otherwise an error will occur. By defining this value to an existing machine group key then machines without a group key already defined in its preferences will be placed into this group. This can be used, for example, to determine which machines have not been setup properly with the correct machine group.

```python
DEFAULT_MACHINE_GROUP_KEY = 'x1eru38unri08badpo0ux4ahz043hapbyqyixdz482l047u9xe60nn6cux1sj0ad5bq7hwblyzjpmaqb17psygfwlfeo4x6hozb1jejaf1nee6paj68glducdt5575dz'
```

## HISTORICAL_FACTS

Normally only the most recent fact is recorded for a machine. Any facts defined here will also have historical data from each run kept in addition to the most recent run.

```python
HISTORICAL_FACTS = [
    'memoryfree_mb',
]
```

## HISTORICAL_DAYS

The number of days to keep historical data. Each historical fact can be recorded once per hour, per fact, per machine. If you have a large number of machines that stay on 24/7 you might consider decreasing this number. Defaults to 180.

```python
HISTORICAL_DAYS = 180
```
