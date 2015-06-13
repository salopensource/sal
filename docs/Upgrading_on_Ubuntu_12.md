Upgrading on Ubuntu 12.04 LTS and 14.04.1 
=====================
This document assumes Ubuntu 12.04 LTS or 14.04.1 and that you have an existing installation of Sal, installed using the [instructions provided](https://github.com/salopensource/sal/blob/master/docs/Installation_on_Ubuntu_12.md). If you don't have an existing installation, you just need to follow the installation instructions.

**If you are upgrading from Sal 1 to Sal 2, please make the following changes to your ``sal/settings.py`` file:**

``` python
BOOTSTRAP3 = {
    'set_placeholder': False,
}
```

And add a line to ``TEMPLATE_CONTEXT_PROCESSORS`` so it looks like:

```python
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "sal.context_processors.display_name",
    "sal.context_processors.config_installed",
)
```

These are in ``sal/example_settings.py`` if you want to copy and paste.

There is also a new plugin: MunkiVersion. To set it's order, add it to ``PLUGIN_ORDER``:

```python
PLUGIN_ORDER = ['Activity','Status','OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory']
```

Under installed apps add 

	'bootstrap3', 
	'api',

and remove 

	'bootstrap-toolkit'
	
and

	'south'
	
Your installed apps should look like this:

```python
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'sal',
    'server',
    'bootstrap3',
    'api',
)
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

Now you have to upgrade the static images

	python manage.py collectstatic

Press yes when asked.

Finally, as root (not saluser) restart Apache

	service apache2 restart
