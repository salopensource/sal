# Sal

Sal is (currently) a reporting dashboard for Munki and optionally, information from Facter.

## Getting Started

First off, you're going to need to get the Server and then the Client installed. [Instructions can be found here](https://github.com/grahamgilbert/sal/blob/master/docs/Installation.md).

Once you've got clients reporting in, you're probably going to want to customise what you see on the various screens. Here's a full list of the various options that can be set in [``sal/settings.py``]((https://github.com/grahamgilbert/sal/blob/master/docs/Settings.md).

After re-ordering and hiding plugins from some screens, you might even want to make your own plugins. At the moment, you'll need to base yours off of the included ones, and my repository of optional ones. I owe you a blog post and some documentation on that, but trust me, it's easy if you know python, and completely possible if you don't.

## Why Sal?

It's the Internet's fault! I asked on Twitter what I should call it, and Peter Bukowinski ([@pmbuko](https://twitter.com/pmbuko)) [suggested the name](https://twitter.com/pmbuko/status/377155523726290944), based on a Monkey puppet called [Sal Minella](http://muppet.wikia.com/wiki/Sal_Minella).