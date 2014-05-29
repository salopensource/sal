Installation on Ubuntu 12.04 LTS
=====================
This document assumes Ubuntu 12.04 LTS. The instructions are largely based on the [CentOS MunkiWebAdmin setup instructions](https://code.google.com/p/munki/wiki/MunkiWebAdminLinuxSetup) by Timothy Sutton.

All commands should be run as root, unless specified.

##Install Prerequisites
###Setup the Virtual Environment

Get your sever up to date:

	apt-get update && apt-get upgrade -y

Make sure git is installed:

	which git
	
If it isn't, isntall it:

	apt-get install git

Install python setup tools:

	apt-get install python-setuptools
	
Make sure virtualenv is installed

	virtualenv --version
	
If it's not, install it:

	easy_install virtualenv==1.10.1

###Create a non-admin service account and group
Create the Sal user:

	useradd saluser
	
Create the Sal group:

	groupadd salgroup
	
Add saluser to the salgroup group:

	usermod -g salgroup saluser

##Create the virtual environment
When a virtualenv is created, pip will also be installed to manage a virtualenv's local packages. Create a virtualenv which will handle installing Django in a contained environment. In this example we'll create a virtualenv for Sal at /usr/local. This should be run from Bash, as this is what the virtualenv activate script expects.

Go to where we're going to install the virtualenv:

	 cd /usr/local
	 
Create the virtualenv for Sal:
	
	virtualenv sal_env
	
Make sure saluser has permissions to the new sal_env folder:

	chown -R saluser sal_env
	
Switch to the service account:
	
	su saluser
	
Virtualenv needs to be run from a bash prompt, so let's switch to one:

	bash
	
Now we can activate the virtualenv:
	
	cd sal_env
	source bin/activate
	
##Copy and configure Sal
Still inside the sal_env virtualenv, use git to clone the current version of Sal

	git clone https://github.com/grahamgilbert/sal.git sal

Now we need to get the other components for Sal

	pip install -r sal/setup/requirements.txt
	
Next we need to make a copy of the example_settings.py file and put in your info:

	cd sal/sal
	cp example_settings.py settings.py
	
Edit settings.py:

* Set ADMINS to an administrative name and email
* Set TIME_ZONE to the appropriate timezone
* Modify DISPLAY_NAME to what you want the header to be
* This is enough to get you going. See [Settings.md](https://github.com/grahamgilbert/sal/blob/master/docs/Settings.md) for more options in detail.

###More Setup
We need to use Django's manage.py to initialise the app's database and create an admin user. Running the syncdb command will ask you to create an admin user - make sure you do this! If you are running Sal in a large environment, it is recommended you use MySQL rather than the default SQLite database. If this is the case, follow the [guide on setting up MySQL before continuing](https://github.com/grahamgilbert/sal/blob/master/docs/Using_mysql_on_ubuntu.md).

####EDIT

It is currently not only recommended that you don't use SQLite, but required. There is a bug with new SQLite installations that we're working on. This bug doesn't exist with Postgres or MySQL.

	cd ..
	python manage.py syncdb
	python manage.py migrate
	
Stage the static files (type yes when prompted)
	
	python manage.py collectstatic

##Installing mod_wsgi and configuring Apache
To run Sal in a production environment, we need to set up a suitable webserver. Make sure you exit out of the Sal_env virtualenv and the saluser user (back to root) before continuing).

	apt-get install libapache2-mod-wsgi
	
##Set up an Apache virtualhost
You will probably need to edit some of these bits to suit your environment, but this works for me. Make a new file at /etc/apache2/sites-available (call it whatever you want)

	nano /etc/apache2/sites-available/sal.conf
	
And then enter something like:

	<VirtualHost *:80>
	ServerName sal.yourdomain.com
   	WSGIScriptAlias / /usr/local/sal_env/sal/sal.wsgi
   	WSGIDaemonProcess sal user=saluser group=salgroup
   	Alias /static/ /usr/local/sal_env/sal/static/
   	<Directory /usr/local/sal_env/sal>
    	   WSGIProcessGroup sal
       		WSGIApplicationGroup %{GLOBAL}
       		Order deny,allow
       		Allow from all
   	</Directory>
	</VirtualHost>
	
Now we just need to enable our site, and then your can go and configure your clients (exit back to root for this):

	a2ensite sal.conf
	service apache2 reload