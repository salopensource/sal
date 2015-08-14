# Using plugins with Sal

It's easy to extend Sal with plugins created by others. A plugin could consist of a "traffic light" display (similar to the built in memory plugin), a listing (e.g. the operating system breakdown), or anything else. I've created plugins that report data in graphs using Google Charts with data from a custom fact.

## Installing plugins

1. Copy the whole plugin directory into the plugins directory. This should include at minimum a ``.py`` file and a ``.yapsy-plugin`` file, but can include more (quite often a ``templates`` directory). For basic operation, all you need to do now is restart Apache and the plugin should appear on your dashboard. If not, head onto the troubleshooting section later on.
2. Head on over to the Settings page (under the person icon in the top bar) and then to Plugins. Enable the plugin by clicking on the checkmark.
3. If you want to control what order the plugins show in, click on the up arrow on the Plugins Settings.

For more details on configuring ``sal/settings.py`` please see it's [documentation](https://github.com/salopensource/sal/blob/master/docs/Settings.md).

## Installing plugins for Heroku

If your installation is on Heroku additional steps are required due to the way Heroku uses git to push updates to the server. The following steps outline how to add the encrypting plugin from my [plugins repo](https://github.com/salopensource/grahamgilbert-plugins):

1. Cd into your sal directory.
2. Clone the plugins from Github.  
	````bash
	git clone https://github.com/salopensource/grahamgilbert-plugins.git plugins/grahamgilbert
	````

3. Remove the gitignore file from the plugins directory.
	````bash
	git rm plugins/.gitignore
	````

4. Add the encryption plugin to the git repo.
	````bash
	git add plugins/grahamgilbert/encryption
	````

5. Add a commit.
	````bash
	git commit -m "add encryption plugin"
	````

6. Push the changes to Heroku.
	````bash
	git push heroku master
	````

*Note*: This plugin relies on the client having the [mac_facts](https://github.com/grahamgilbert/grahamgilbert-mac_facts) custom Facts installed, either through Puppet's built in plugin sync (if using Puppet), or by installing the package following [facts-package](https://github.com/salopensource/grahamgilbert-plugins/blob/master/encryption/facts-package/sal_mac_facts.pkg).

## Troubleshooting

###  I'm not seeing anything after installing the plugin

There are a few reasons you might not get any output from the plugin.

* The plugin might be set to not display anything if there isn't anything for it to show (the Fact or Condition it relies on isn't available, or there aren't any updates to install, for example).
* If you are sure that it should be showing something, then you should check that it's in the correct directory, and that it's readable and executable by the user the application is running as (saluser if you followed the instructions here).
* If you're still having problems, then there may be something wrong with the plugin. You should contact the person who wrote the plugin for more assistance - their contact details will hopefully be in the .yapsy-plugin file.
