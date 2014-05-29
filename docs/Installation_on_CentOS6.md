Installation on CentOS 6
=====================

These instructions are largely based on the Python 2.7 guide on [Too Much Data](http://toomuchdata.com/2014/02/14/how-to-install-modern-python-on-centos-6/) and the [MunkiWebAdmin install guide](https://code.google.com/p/munki/wiki/MunkiWebAdminLinuxSetup).

All commands should be run as root, unless specified (via ``su -``).

##Install Prerequisites

### Install Python 2.7

The version of Python that ships with CentOS (2.6) is too old for Sal to run properly, so we are going to install a more up to date one.

Install the development tools:

	yum update
	yum groupinstall "Development tools"
	yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel python-devel httpd-devel gcc
	
Open up ``/etc/ld.so.conf``:
	
	nano /etc/ld.so.conf
	
And make it add the line at the end to make it look like:

	include ld.so.conf.d/*.conf
	/usr/local/lib

Make the OS aware of the change:

	/sbin/ldconfig
	
Download and install Python:

	cd /tmp
	wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
	tar xf Python-2.7.6.tar.xz
	cd Python-2.7.6
	./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
	make && make altinstall

###Setup the Virtual Environment

Make sure git is installed:

	which git
	
If it isn't, install it:

	yum install git

Download and install python setup tools:

	cd /tmp
	wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
	python2.7 ez_setup.py
	
Install Pip

	easy_install-2.7 pip

Install virtualenv

	pip2.7 install virtualenv==1.10.1

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
	
	virtualenv-2.7 sal_env
	
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
We need to use Django's manage.py to initialise the app's database and create an admin user. Running the syncdb command will ask you to create an admin user - make sure you do this! If you are running Sal in a large environment, it is recommended you use MySQL rather than the default SQLite database. If this is the case, follow the [guide on setting up MySQL before continuing](https://github.com/grahamgilbert/sal/blob/master/docs/Using_mysql_on_CentOS6.md).

####EDIT

It is currently not only recommended that you don't use SQLite, but required. There is a bug with new SQLite installations that we're working on. This bug doesn't exist with Postgres or MySQL.

	cd ..
	python manage.py syncdb
	python manage.py migrate
	
Stage the static files (type yes when prompted)
	
	python manage.py collectstatic

##Installing mod_wsgi and configuring Apache
To run Sal in a production environment, we need to set up a suitable webserver. Make sure you exit out of the Sal_env virtualenv and the saluser user (back to root) before continuing).

	yum install httpd httpd-devel
	chkconfig httpd on
	service httpd start

Now we need to install mod_wsgi:

	cd /usr/local/lib/python2.7/config/
	ln -s ../../libpython2.7.so .
	cd /tmp
	wget https://modwsgi.googlecode.com/files/mod_wsgi-3.4.tar.gz
	tar xf mod_wsgi-3.4.tar.gz && cd mod_wsgi-3.4
	export LD_LIBRARY_PATH=/usr/local/lib
	./configure --with-apxs=/usr/sbin/apxs --with-python=/usr/local/bin/python2.7
	make && make install

Now we're going to tell Apache about our new module.
	
	nano /etc/httpd/conf/httpd.conf

And add in:

	LoadModule wsgi_module modules/mod_wsgi.so

And restart Apache:

	service httpd restart
	
##Set up an Apache virtualhost
You will probably need to edit some of these bits to suit your environment, but this works for me. Make a new file at /etc/apache2/sites-available (call it whatever you want)

	nano /etc/httpd/conf.d/sal.conf
	
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
       		Allow from all
   	</Directory>
	</VirtualHost>
	
Now we just need to enable our site, and then your can go and configure your clients (exit back to root for this):

	service httpd restart

If you can't connect, make sure you're allowing port 80 through the firewall:

	iptables -I INPUT -p tcp --dport 80 -j ACCEPT
	service iptables save
