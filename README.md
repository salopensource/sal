# Sal

[![CircleCI](https://circleci.com/gh/salopensource/sal.svg?style=svg)](https://circleci.com/gh/salopensource/sal)

Sal is a multi-tenanted reporting dashboard for [Munki](https://github.com/munki/munki/) with the ability to display information from [Facter](https://puppet.com/docs/puppet/latest/facter.html). It has a plugin system allowing you to easily build widgets to display your custom information from Facter, Grains, Munki's [conditional items](https://github.com/munki/munki/wiki/Conditional-Items) etc.

With Sal, you are able to allow access to reports on certain sets of machines to certain people - for example, giving a manager access to the reports on the machines in their department.

Sal also features powerful search capabilities and application inventory and support for Munki's license tracking.

![Sal](https://github.com/salopensource/sal/raw/main/assets/Sal.png)

## Getting Started

First off, you're going to need to get the Server and then the Client component of Sal installed. [Instructions can be found here](https://github.com/salopensource/sal/wiki/Getting-Started).

Once you've got clients reporting in, you're probably going to want to customise what you see on the various screens. [Here is a full list](https://github.com/salopensource/sal/wiki/Settings) of the various options that can be set in `sal/settings.py`.

If you would like a demo of setting up Sal along with some of the features please watch the following presentation Graham made at the 2014 [Penn State MacAdmins Conference](http://youtu.be/BPTJnz27T44?t=21m28s). Slides available from [here](http://grahamgilbert.com/images/posts/2014-07-09/Multi_site_Munki.pdf).

## Search

Sal has full search across machines, Facts and Munki conditions. For more information, see [it's documentation](https://github.com/salopensource/sal/wiki/Search).

![Search](https://github.com/salopensource/sal/raw/main/assets/Built%20search.png)

## Plugins

You can enable, disable and re-order your plugins from the Settings page, under the 'person' menu in the main menu bar. For more information on using and installing your own plugins, visit the [Using Plugins](https://github.com/salopensource/sal/wiki/Installing-and-using-plugins) page.

After re-ordering and hiding plugins from some screens, you might even want to make your own plugins. You can base your plugin off of one of the included ones, or one of mine in the [repository of optional plugins](https://github.com/salopensource/grahamgilbert-plugins). For more information on writing plugins, check out the [wiki](https://github.com/salopensource/sal/wiki).

## External Authentication

There is a variant of Sal that supports [SAML](https://github.com/salopensource/sal/pkgs/container/sal-saml)authentication.

## Having problems?

You should check out the [troubleshooting](https://github.com/salopensource/sal/wiki/Troubleshooting) page, consider heading over the the #sal channel on the [macadmins.org Slack](http://macadmins.org).

## API

There is a simple API available for Sal. Documentation can be found at [docs/Api.md](https://github.com/salopensource/sal/wiki/API)

## Why Sal?

It's the Internet's fault! I asked on Twitter what I should call it, and Peter Bukowinski ([@pmbuko](https://twitter.com/pmbuko)) [suggested the name](https://twitter.com/pmbuko/status/377155523726290944), based on a Monkey puppet called [Sal Minella](http://muppet.wikia.com/wiki/Sal_Minella).
