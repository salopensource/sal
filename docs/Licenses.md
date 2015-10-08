Licenses
========

Sal implements [Munki's license tracking](https://github.com/munki/munki/wiki/License-Seat-Tracking). Sal will try to match on as much information as you give it - it is looked up from submitted inventory by clients.

## Setting up licenses

Navigate to Settings -> Licenses from the top menu. When you choose to add a license, you will be able to fill in the information about the license. Cost is for your use only - it is not used by Sal at this time. Item Name is the name you have given the item  in your Munki repository, and the rest of the fields correlate to their respecitve fields in the inventory. As previously stated, Sal performs an ``AND`` search when you add more information to a license - if you just put in the Bundle ID, that's all that will be matched. If you put in a version, that will be matched as well.

### A note on versions

The version field supports wildcards - finish your version number with a ``*`` if you wish to use this.

## Configuration

As per the Munki Wiki, you will need to configure ``LicenseInfoURL`` in your ``ManagedInstalls`` preferences. This should be set to:

```
http://sal/licenses/available/MACHINEGROUPKEY/
```

Where ``MACHINEGROUPKEY`` is that machine's group.