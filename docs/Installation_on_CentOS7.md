Installation on CentOS 7
=====================

Unlike previous CentOS releases, 7 ships with Python 2.7.5 and thus a number of the initial steps from [the install Sal on CentOS6 guide](https://github.com/salopensource/sal/blob/master/docs/Installation_on_CentOS6.md) can be skipped.

These instructions were done using CentOS 7 x86 64bit Minimal Installation in a clean VM.

All commands should be run as root, unless specified (via ``su -``).

##Install Prerequisites

###Update System and Install Development Tools

Using sudo to become root is a lot easier than typing each line with sudo at the beginning, just remember you are **root** so watch your step:

	sudo -s

Install/update the development tools:

	yum update
	yum groupinstall "Development tools"

New for Sal2 we need a few more things (these remove missing ffi.h and openssl/aes.h errors):

	yum install libffi-devel openssl-devel

If you're not comfortable with emacs/vi, lets make sure at least nano (or some other editor you know) is installed:

	yum install nano

###Setup the Virtual Environment

Git is installed by default, but let's double-check it's there, just in case:

	which git
	
However, if it isn't, install it:

	yum install git

Install Pip:

	easy_install pip

Install virtualenv:

	pip install virtualenv==1.10.1

###Create a non-admin service account and group
Create the Sal user:

	useradd saluser
	
Create the Sal group:

	groupadd salgroup
	
Add saluser to the salgroup group:

	usermod -g salgroup saluser

##Create the Virtual Environment
When a virtualenv is created, pip will also be installed to manage a virtualenv's local packages. We'll create a virtualenv which will handle installing Django in a contained environment. In this example we'll create a virtualenv for Sal at /usr/local. This should be run from Bash, as this is what the virtualenv activate script expects.

Go to where we're going to install the virtualenv:

	 cd /usr/local
	 
Create the virtualenv for Sal:
	
	virtualenv sal_env
	
Make sure saluser has permissions to the new sal_env folder:

	chown -R saluser sal_env
	
Switch to the saluser account:
	
	su saluser
	
Virtualenv needs to be run from a Bash prompt, CentOS should have made Bash the default shell for the saluser but just in case:

	bash
	
Now we can activate the virtualenv:
	
	cd sal_env
	source bin/activate
	
##Copy and Configure Sal
Still inside the sal_env virtualenv, use git to clone the current version of Sal:

	git clone https://github.com/salopensource/sal.git sal

Now we need to get the other components for Sal

	pip install -r sal/setup/requirements.txt
	
Next we need to make a copy of the example_settings.py file and put in your info:

	cd sal/sal
	cp example_settings.py settings.py
	
Edit settings.py:

	nano -w settings.py

* Set ADMINS to an administrative name and email
* Set TIME_ZONE to the appropriate timezone
* Modify DISPLAY_NAME to what you want the header to be
* This is enough to get you going. See [Settings.md](https://github.com/salopensource/sal/blob/master/docs/Settings.md) for more options in detail.

###More Setup
We need to use Django's manage.py to initialize the app's database and create an admin user. Running the syncdb command will ask you to create an admin user - make sure you do this! If you are running Sal in a large environment, it is recommended you use MySQL rather than the default SQLite database. If this is the case, follow the [guide on setting up MySQL before continuing](https://github.com/salopensource/sal/blob/master/docs/Using_mysql_on_CentOS6.md).

	cd ..
	python manage.py syncdb
	python manage.py migrate
	
Stage the static files (type yes when prompted)
	
	python manage.py collectstatic

Now exit (ctrl-d) back to the root user for the final steps.  You may need to do so twice if your prompt still shows ``[saluser@`` instead of ``[root@``:

	exit

##Installing Apache and mod_wsgi
To run Sal in a production environment, we need to set up a suitable webserver. Make sure you exit out of the Sal_env virtualenv and the saluser user (back to root) before continuing.  Installing mod_wsgi will cause yum to also install Apache (httpd) if needed:

	yum install mod_wsgi
	systemctl enable httpd
	systemctl start httpd

##Set up an Apache VirtualHost
You will probably need to edit some of these bits to suit your environment, but this works for me. Make a new file at /etc/httpd/con.d/ (call it whatever you want)

	nano -w /etc/httpd/conf.d/sal.conf
	
And then enter something like:


	WSGISocketPrefix /var/run/wsgi
	<VirtualHost *:80>
	  ServerName sal.yourdomain.com
	  WSGIScriptAlias / /usr/local/sal_env/sal/sal.wsgi
	  WSGIDaemonProcess sal user=saluser group=salgroup
	  Alias /static/ /usr/local/sal_env/sal/static/
	  <Directory /usr/local/sal_env/sal>
	    WSGIProcessGroup sal
	    WSGIApplicationGroup %{GLOBAL}
	    Order deny,allow
	    Require all granted
	  </Directory>
	</VirtualHost>


If Sal is the **only** site on this webserver you'll also need to edit Apache's conf:

	nano -w /etc/httpd/conf/httpd.conf

search for: 

	<Directory />
	       AllowOverride allow,deny
	       Require all granted
	</Directory>

and comment the lines out by changing them to:

	#<Directory />
	#       AllowOverride allow,deny
	#       Require all granted
	#</Directory>

Run a quick syntax and sanity-check on our changes to Apache:

	apachectl configtest

Now we just need to enable our site, and then can go and configure the clients:

	systemctl restart httpd

That's it, now go login with the admin user and pass created earlier during manage.py steps, we're done here.

But if it's not working...

##Troubleshooting

If you can't connect, make sure you're allowing port 80 through the firewall, these commands will permanently allow access to port 80, or whatever you have chosen by adjusting accordingly, and will survive reboots:

	firewall-cmd --zone=public --add-port=80/tcp --permanent
	firewall-cmd --reload


If you're getting "Page unavailable" on first connect try running Apache in single-thread mode:

	systemctl stop httpd
	httpd -X

If that works, albeit extremely slowly, then you likely have an SELinux issue, you can confirm SELinux is enabled and enforcing by running:

	sestatus

It can be disabled by editing /etc/selinux/config changing:

	SELINUX=enforcing
	
to:

	SELINUX=disabled

and rebooting - yes, **a full reboot is required** to disable SELinux.

	reboot


If you can connect in a browser but aren't seeing a login screen, try increasing apache's logging level **temporarily** to have more information about what's going on:

	nano -w /etc/httpd/conf/httpd.conf

search for:

	LogLevel warn

and change it to:

	LogLevel info

and restart Apache:

	systemctl restart httpd

then to monitor the logs while you attempt to connect you can use:

	tail -f /var/log/httpd/error_log

and hopefully something there points you toward the problem if it's not the firewall and SELinux listed above.

If you are migrating to Sal2 and get errors during ``pip install -r sal/setup/requirements.txt`` about missing ffi.h and/or openssl/aes.h the fix is to install the development packages for libffi and openssl as follows:

	yum install libffi-devel openssl-devel
