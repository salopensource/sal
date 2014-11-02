# Sal

## How it works

Sal is split into Business Units, and then subdivided into Groups. Each customer would be a Business Unit, and then the machines can be divided into Machine Groups.

##Server installation/upgrade

The recommended (and easiest) way of getting running on your own hardware is using [Docker](https://github.com/salsoftware/sal/blob/master/docs/Docker.md).

If you aren't comfortable with Linux, it's recommended that your [first installation is on Heroku](https://github.com/salsoftware/sal/blob/master/docs/Deploying_on_Heroku.md) which will handle the server configuration for you.

If you plan on installing on your own hardware, see [Installation on Ubuntu 12](https://github.com/salsoftware/sal/blob/master/docs/Installation_on_Ubuntu_12.md) (or [CentOS](https://github.com/salsoftware/sal/blob/master/docs/Installation_on_CentOS6.md)) for server installation docs. If you are installing on a different operating system, please ensure you have Python 2.7 installed.

See [Upgrading on Ubuntu 12](https://github.com/salsoftware/sal/blob/master/docs/Upgrading_on_Ubuntu_12.md) for upgrade docs.

## Getting started

You will need to have the server component of Sal setup before continuing to the following steps. Log in with the username and password you set when performing the server setup. You will need to create a Business Unit and Machine Group to get started.

### User Levels

There are currently three User Levels used by Sal. To set these, log into the admin page (link at the top of the Sal screen), and choose User Profile from the menu.

**1. Global Administrator**

A Global Administrator (GA) has access to everything - they can get into all Business Units, they can create new Business Units and Machine Groups. They cannot get to the admin interface though. To do this, they need to be added to the staff group (in the Users section of the admin interface).

**2. Read / Write, Read Only**

These users are limited to the Business Units they are given access to. Read/Write users can create new Machine Groups within their Business Units, Read Only users are only able to view the information.

**3. Stats Only**

The Stats Only user level is not used at this time, and should *not* be assigned to a user.

## Client configuration

The sal ``postflight`` script needs to be deployed in the ``/usr/local/munki`` directory, and the ``yaml`` directory should be deployed in ``/usr/local/sal/yaml`` (a luggage makefile is included). Alternately, you can use the [published package](https://github.com/salsoftware/sal/releases/latest) to deploy the necessary client files.

If you have an existing ``postflight`` script (for example, Munki Web Admin), you will need to rename the sal postflight script (for example, ``sal-submit``) and add a reference in your existing postflight like this:

``` bash
if [ -f /usr/local/munki/sal-submit ]
  then
    /usr/local/munki/sal-submit
fi
```

The configuration of the Server Address, and the Machine Group key is from ``/Library/Preferences/com.grahamgilbert.sal``. Plists, MCX (untested, but should work) and Profiles can be used.

### Manual Client Conf. Example

If you wish to set the Server Address and Machine Group Key via defaults you can do so with the following examples (root is needed):

``defaults write /Library/Preferences/com.grahamgilbert.sal ServerURL http://sal.somewhere.com``

``defaults write /Library/Preferences/com.grahamgilbert.sal key e4up7l5pzaq7w4x12en3c0d5y3neiutlezvd73z9qeac7zwybv3jj5tghhmlseorzy5kb4zkc7rnc2sffgir4uw79esdd60pfzfwszkukruop0mmyn5gnhark9n8lmx9``

### Using custom Facts

If you are using [Puppet](http://puppetlabs.com) to manage your Macs, you can deploy custom Facts in the usual manner using pluginsync. If you're not using Puppet, you can still utilise custom Facts. You should deploy the ``.rb`` files to ``/usr/local/sal/facter``. If you want to use [external Facts](http://docs.puppetlabs.com/guides/custom_facts.html#external-facts), you can deploy them to the usual location (``/etc/facter/facts.d/``).
