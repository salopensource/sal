# Sal

Sal is (currently) a multi-tennanted reporting dashboard for [Munki](https://code.google.com/p/munki/) and optionally, information from [Facter](http://puppetlabs.com/facter). It has a plugin system allowing you to easily build widgets to display your custom information from Facter or Munki's [conditional items](https://code.google.com/p/munki/wiki/ConditionalItems) (or both!). 

With Sal, you are able to allow access to reports on certain sets of machines to certain people - for example, giving a manager access to the reports on the machines in their department.

![Sal](docs/img/Sal.png)

## Getting Started

First off, you're going to need to get the Server and then the Client installed. [Instructions can be found here](https://github.com/grahamgilbert/sal/blob/master/docs/Installation.md).

Once you've got clients reporting in, you're probably going to want to customise what you see on the various screens. [Here is a full list](https://github.com/grahamgilbert/sal/blob/master/docs/Settings.md) of the various options that can be set in ``sal/settings.py``.

After re-ordering and hiding plugins from some screens, you might even want to make your own plugins. At the moment, you'll need to base yours off of the included ones, and my [repository of optional ones](https://github.com/grahamgilbert/sal-plugins). I owe you a blog post and some documentation on that, but trust me, it's easy if you know python, and completely possible if you don't.

## Why Sal?

It's the Internet's fault! I asked on Twitter what I should call it, and Peter Bukowinski ([@pmbuko](https://twitter.com/pmbuko)) [suggested the name](https://twitter.com/pmbuko/status/377155523726290944), based on a Monkey puppet called [Sal Minella](http://muppet.wikia.com/wiki/Sal_Minella).

## Thank yous

First off, thanks to Greg Neagle and the rest of the Munki Project. This started off using quite a lot of Munki Web Admin's code (and still contains portions of it). Munki is an amazing product, and managing OS X at any scale would be miserable without it.

Thanks to Puppet Labs for basically giving away the crown jewels for nothing.

And finally, thanks to my lovely employers, [pebble.it](http://pebbleit.com) for letting me release this. They could just as easily have told me that this was staying in house, but they believe in open source as much as I do (did I mention they were lovely?).