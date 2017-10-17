(This will end up in the wiki, this is just here so we can work on it in the meantime)

There are existing agents for Sal for both macOS and Windows, but if you wish to build a reporting agent for another platform, the sent data should be in the following format.

If the server has basic authentication enabled (which is the default), you should use the username `sal` and the password will be the client’s key.

The data here is represented as a Python dictionary, you should extrapolate the data structure for the language you are writing the agent in.

```
{
    # This needs to be unique for each run. uuidgen on macOS is great for this
    'run_uuid': 'e38e3237-50c9-41d7-b0fa-86be834bd766’,
    # This is the total disk size in
    'disk_size': 976163048,
    'name': u'thunderpants',
    'key': u'yourveryveryverylongkey',
    'sal_version': '2.0.4',
    # The serial number must be unique - it is the unique key for a checkin
    'serial': u'SOMESERIALNUMBERMUSTBEUNIQUE',
    # Choose one of the following
    'base64report': 'your base64 encoded report',
    'base64bz2report': 'your base64, bzip2 compressed report'
}
```

## The report
The report should start life as a plist. How you generate this is up to you (python, go and javascript have libraries for generating these). The plist should then either be just base 64 encoded, or b2zipped, then base 64 encoded. If your platform supports b2zip, it is suggested that you utilize it.

Sal supports two formats for `MachineInfo` - this can either be in the data structure you get from System Profiler on macOS (under the `SystemProfile` key), or you can use the following fields within a `HardwareInfo` dictionary.

```
'MachineInfo':
{   
    'os_vers': 'Windows ABC Release l33t',
    # Available disk space, in KB (integer)
    'AvailableDiskSpace': 1230,
    # Total disk size, in KB (integer)
    'disk_size': 50000,
    # One of 'Darwin', 'Windows', 'Linux'
    'os_family': 'Windows',
    'HardwareInfo': {
        'machine_model': 'The model of your computer',
        'cpu_type': 'x86 etc',
        'current_processor_speed': '20Ghz',
        # This must end with ' KB', ' MB', ' GB' or ' TB' - note the space at the end
        'physical_memory': '16 GB',
    }
}
```
