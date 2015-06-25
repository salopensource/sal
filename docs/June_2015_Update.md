Applying the June 2015 Update
======================

If you have a new installation of Sal, or you started with Sal after the June 2015 update (the migration to the ``salopensource`` organisation on GitHub), you **do not need to do this. Stop now.**

The June 2015 update contains a significant upgrade to Django (the core framework that runs Sal) - this contains lots of bug fixes and security patches (a 'good thing'). But you do need to perform one extra step after performing your normal update procedure (either following [this guide](https://github.com/salopensource/sal/blob/master/docs/Upgrading_on_Ubuntu_12.md) if you are running using the older method of deploying Sal, or after ``docker pull macadmins/sal`` if you are using Docker).

It is recommended that you start with a fresh ``sal/settings.py`` (copied from ``sal/example_settings.py``), as there have been quite a few changes.

You only need to perform the following once.

# Docker

Stop and remove your Sal container:

```
$ docker stop sal
$ docker rm sal
```

We're now going to run a temporary container to update the database - if you have any custom mounts (e.g. ``settings.py`` or plugins), you should include them as you normally would, and replace the DB_* environment variables to match what you have used:

```
$ docker run -t -i --rm --link postgres-sal:db -e DB_NAME=sal -e DB_USER=admin -e DB_PASS=password macadmins/sal /bin/bash
# We're in the container now
$ cd /home/app/sal
$ python manage.py migrate --fake-initial
$ exit
```

# Legacy (Apache)

```
$ source /usr/local/sal_env/bin/activate
$ cd /usr/local/sal_env/sal
$ python manage.py migrate --fake-initial
```

# Plugins

If you have used custom plugins, make sure they are compatible with the change. The primary change is any reference to ``fact`` becomes ``facts``.

``` python
ok = machines.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1).count()
```

Becomes:

``` python
ok = machines.filter(facts__fact_name='uptime_days', facts__fact_data__lte=1).count()
```
