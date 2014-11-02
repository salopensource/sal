# Configuring Sal to use Mysql

## Install MySQL and create a database

First we will install MySQL and create database, database user and give privileges for that user to the database. Be sure to modify DATABASENAME with the database name of your choice, DATABASEUSER with the database username of your choice and of course PASSWORD with the password for that database user. So, as root:

``` bash
apt-get -y install mysql-server mysql-client
echo "CREATE DATABASE DATABASENAME;" | mysql -u root -p
echo "CREATE USER 'DATABASEUSER'@'localhost' IDENTIFIED BY 'PASSWORD';" | mysql -u root -p
echo "GRANT ALL PRIVILEGES ON DATABASENAME.* TO 'DATABASEUSER'@'localhost';" | mysql -u root -p
echo "FLUSH PRIVILEGES;" | mysql -u root -p
```

## Get MySQL working with Python

We need to install some dependencies before we can plug Sal into MySQL. As root:

``` bash
apt-get build-dep python-mysqldb
```

Now switch to your saluer and activate the virtualenv:

``` bash
su saluser
bash
cd /usr/local/sal_env
source bin/activate
```

Now one last piece to install:

``` bash
pip install MySQL-python
```

## Tell Sal about your database

We need to edit ``/usr/local/sal_env/sal/sal/settings.py``. Make the database section look like the below, substituting your database name, username and password:

``` python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'DATABASENAME',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'DATABASEUSER',
        'PASSWORD': 'PASSWORD',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}
```

Now you can return to the rest of the [installation guide](https://github.com/salsoftware/sal/blob/master/docs/Installation_on_Ubuntu_12.md).
 