Migrating Sal to Docker
========
I have an existing Sal instance installed on a server somewhere.  I've heard about this Docker thing and now I want to do something cool with it. How do I get my existing data from Sal into a Docker instance?

On your original Sal host:
----
1. Navigate to your Sal location: `cd /usr/local/sal_env/`
2. Activate your virtualenv: `source bin/activate`
3. `cd sal`
4. `python manage.py dumpdata --format json > saldata.json`
5. Copy the saldata.json file to the Docker host.

Setup your Docker host:
-----
1. Install Docker (as you'd expect).
2. `docker pull grahamgilbert/postgres`
   *  We're using Postgres simply because it's recommended.
3. `docker pull macadmins/sal`
4. `mkdir -p /usr/local/sal_data/settings/`
5. Obtain the settings.py from the Sal github:
   `curl -o /usr/local/sal_data/settings/settings.py https://raw.githubusercontent.com/macadmins/sal/master/settings.py`
6. Start your Postgres Docker container:
   `docker run --name "postgres-sal" -d -v /usr/local/sal_data/db:/var/lib/postgresql/data postgres`
7. Copy the saldata.json file into a directory called "saldata". In this example, I created this in my home.
8. `docker run --name "sal-loaddata" --link postgres-sal:db -e ADMIN_PASS=pass -e DB_NAME=sal -e DB_USER=saldbadmin -e DB_PASS=pass -i -t --rm -v /home/nmcspadden/saldata:/saldata -v /usr/local/sal_data/settings/settings.py:/home/docker/sal/sal/settings.py macadmins/sal /bin/bash`
    * Several things happening in this example. First, we're linking the local "saldata" directory into the container so it can access the Sal dump at /saldata/saldata.json.  
    * Seecond, we're linking in our custom 'settings.py' file. If you didn't make any modifications or add custom apps, you may not need to do this.
    * Make sure your ADMIN_PASS, DB_NAME, DB_USER, and DB_PASS match what you did in setup_db.sh.
    * Last, we're running an interactive shell on this container so we can load the data.

Inside the "sal-loaddata" Docker container:

1. `cd /home/docker/sal`
2. `python manage.py loaddata /saldata/saldata.json`
3. `exit` when done to remove the container.

Run Sal!
----
Final step:
  `docker run -d --name="sal" -p 80:8000 --link postgres-sal:db -e ADMIN_PASS=pass -e DB_NAME=sal -e DB_USER=saldbadmin -e DB_PASS=pass -v /usr/local/sal_data/settings/settings.py:/home/docker/sal/sal/settings.py macadmins/sal`

Now you can access Sal via your web browser, using your old user account and password, with all existing data migrated.
