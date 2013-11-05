# Sal

## How it works

Sal is split into Business Units, and then subdivided into Groups. Each client would be a Business Unit, and then each Munki manifest is a Group. 

##Server installation

See ``Installation_on_Ubuntu_12.md`` for server installation docs.

### Getting started

You will need to set your user level in the UserProfile to Global Admin to get started (go to ``http://your_sal_box/admin/``). Create a Business Unit, and then create a Group that is associated with the Munki manifest.

## Client configuration

``sal-submit`` is in the ``scripts`` directory. This, along with the contents of the ``yaml`` directory need to be deployed in ``/usr/local/munki`` (a luggage makefile is included). At this time, it is expected that Facter is installed as well.

If you have an existing ``postflight`` script (for example, Munki Web Admin), you will need to put something in it like this:

```
if [ -f /usr/local/munki/sal-submit ]
  then
    /usr/local/munki/sal-submit
fi
```

If not, simply rename ``sal-submit`` to ``postflight``

The configuration of the server, and the Business Unit key is from ``/Library/Preferences/com.grahamgilbert.sal``. Plists, MCX (untested, but should work) and Profiles can be used.

### Example

``defaults write /Library/Preferences/com.grahamgilbert.sal ServerURL http://sal.somewhere.com``

``defaults write /Library/Preferences/com.grahamgilbert.sal key e4up7l5pzaq7w4x12en3c0d5y3neiutlezvd73z9qeac7zwybv3jj5tghhmlseorzy5kb4zkc7rnc2sffgir4uw79esdd60pfzfwszkukruop0mmyn5gnhark9n8lmx9``

