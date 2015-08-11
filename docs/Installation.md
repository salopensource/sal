# Sal

## How it works

Sal is split into Business Units, and then subdivided into Groups. Each customer would be a Business Unit, and then the machines can be divided into Machine Groups.

##Server installation/upgrade

The recommended (and easiest) way of getting running on your own hardware is using [Docker](https://github.com/salopensource/sal/blob/master/docs/Docker.md). In future versions of Sal, this will be the only supported method of deploying in your own data centre, so it is highly recommended you get to grips with it.

If you aren't comfortable with Linux, it's recommended that your [first installation is on Heroku](https://github.com/salopensource/sal/blob/master/docs/Deploying_on_Heroku.md) which will handle the server configuration for you.

If you plan on installing on your own hardware, see [Installation on Ubuntu 12](https://github.com/salopensource/sal/blob/master/docs/Installation_on_Ubuntu_12.md) (or [CentOS](https://github.com/salopensource/sal/blob/master/docs/Installation_on_CentOS6.md) or [Ubuntu 14](https://github.com/salopensource/sal/blob/master/docs/Installation_on_Ubuntu_14.md)) for server installation docs. If you are installing on a different operating system, please ensure you have Python 2.7 installed.

See [Upgrading on Ubuntu 12](https://github.com/salopensource/sal/blob/master/docs/Upgrading_on_Ubuntu_12.md) for upgrade docs.

If you are running a manual installation and would like to migrate to Docker, please see the [migration document](https://github.com/salopensource/sal/blob/master/docs/DockerMigration.md) written by Nick McSpadden.

## Getting started

You will need to have the server component of Sal setup before continuing to the following steps. Log in with the username and password you set when performing the server setup. You will need to create a Business Unit and Machine Group to get started.

### User Levels

There are currently three User Levels used by Sal. To set these, log into the admin page (link at the top of the Sal screen), and choose User Profile from the menu.

**1. Global Administrator**

A Global Administrator (GA) has access to everything - they can get into all Business Units, they can create new Business Units and Machine Groups. They cannot get to the admin interface though. To do this, they need to be added to the staff group (in the Users section of the admin interface).

**2. Read / Write, Read Only**

These users are limited to the Business Units they are given access to. Read/Write users can create new Machine Groups and Machines within their Business Units, Read Only users are only able to view the information.

**3. Stats Only**

The Stats Only user level is not used at this time, and should *not* be assigned to a user.

## Client configuration

The sal ``postflight`` script needs to be deployed in the ``/usr/local/munki`` directory, and the ``yaml`` directory should be deployed in ``/usr/local/sal/yaml`` (a luggage makefile is included). Alternately, you can use the [published package](https://github.com/salopensource/sal-scripts/releases/latest) to deploy the necessary client files. There is also an [AutoPkg recipe](https://github.com/autopkg/grahamgilbert-recipes/tree/master/Sal).

If you have an existing ``postflight`` script (for example, Munki Web Admin), you will need to rename it (for example, ``mwa-submit``) and move it into ``/usr/local/munki/postflight.d``:

The configuration of the Server Address, and the Machine Group key is from ``/Library/Preferences/com.github.salopensource.sal``. Plists, MCX (untested, but should work) and Profiles can be used.

It is recomended that both Facter and osquery are configured on the client machine, although both are optional. Facter will work with no additional configuration, but osquery will need some additional setup. If you aren't currently using osquery (so have no configuration to save), you can use the package at [PACKAGE WILL GO HERE]. If you are integrating Sal with an existing osquery setup, you will need to add ``"log_result_events": "false"`` to the ``options`` section of your configuration file:

``` json /var/osquery/osquery.conf
{
  "options": {
    "host_identifier": "uuid",
    "log_result_events": "false",
    "schedule_splay_percent": 10
  },

  "schedule": {
    },


  "packs": {
  }
}
```

The Sal preflight script will create the needed configuration in ``/var/osquery/osquery.conf.d``. If you wish to manage this manually, you should disable the preflight script (not recommended).

### Manual Client Conf. Example

If you wish to set the Server Address and Machine Group Key via defaults you can do so with the following examples (root is needed):

``defaults write /Library/Preferences/com.github.salopensource.sal ServerURL http://sal.somewhere.com``

``defaults write /Library/Preferences/com.github.salopensource.sal key e4up7l5pzaq7w4x12en3c0d5y3neiutlezvd73z9qeac7zwybv3jj5tghhmlseorzy5kb4zkc7rnc2sffgir4uw79esdd60pfzfwszkukruop0mmyn5gnhark9n8lmx9``

### Using custom Facts

If you are using [Puppet](http://puppetlabs.com) to manage your Macs, you can deploy custom Facts in the usual manner using pluginsync. If you're not using Puppet, you can still utilise custom Facts. You should deploy the ``.rb`` files to ``/usr/local/sal/facter``. If you want to use [external Facts](http://docs.puppetlabs.com/guides/custom_facts.html#external-facts), you can deploy them to the usual location (``/etc/facter/facts.d/``).
