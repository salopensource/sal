Upgrading on Ubuntu 12.04 LTS
=====================
This document assumes Ubuntu 12.04 LTS and that you have an existing installation of Sal, installed using the [instructions provided](https://github.com/grahamgilbert/sal/blob/master/docs/Installation_on_Ubuntu_12.md). If you don't have an existing installation, you just need to follow the installation instructions.

**If you are upgrading from Sal 1 to Sal 2, please add the following to your ``sal/settings.py`` file:**

``` python
BOOTSTRAP3 = {
    'set_placeholder': False,
}
```

This is in ``sal/example_settings.py`` if you want to copy and paste.

There is also a new plugin: MunkiVersion. To set it's order, add it to ``PLUGIN_ORDER``:

```python
PLUGIN_ORDER = ['Activity','Status','OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory']
```

##Upgrade guide
Switch to the service account

	su saluser
	
Start bash

	bash
	
Change into the Sal virtualenv directory
	
	cd /usr/local/sal_env

Activate the virtualenv

	source bin/activate

Change into the Sal directory and update the code from GitHub

	cd sal
	git pull
	
Install any extra dependencies:
	
	pip install -r setup/requirements.txt
	
Run the migration so your database is up to date
	
	python manage.py migrate
	
If you get errors about a failed migration, run ``python manage.py migrate`` again. Some errors are just temporary.

Finally, as root (not saluser) restart Apache

	service apache2 restart
