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
2. `docker pull postgres`
   *  We're using Postgres simply because it's recommended.
3. `docker pull macadmins/sal`
4. Obtain the setup_db.sh script from the Sal github: 
  `curl -o https://raw.githubusercontent.com/macadmins/sal/master/setup_db.sh`
5. `chmod +x setup_db.sh`
6. `mkdir -p /usr/local/sal_data/settings/`
7. Obtain the settings.py from the Sal github:
   `curl -o /usr/local/sal_data/settings/settings.py https://raw.githubusercontent.com/macadmins/sal/master/settings.py`
8. If you need to make any changes, such as importing extra apps like [WHDImport](https://github.com/nmcspadden/Sal-WHDImport), edit the settings.py file now.
   * If you're adding WHDImport, then just add 'whdimport' to the list of INSTALLED_APPS in settings.py.
   * If you plan to add WHDImport, you'll also need to clone that in: `git clone https://github.com/nmcspadden/Sal-WHDImport.git /usr/local/sal_data/whdimport`
9. Start your Postgres Docker container:
   `docker run --name "postgres-sal" -d -v /usr/local/sal_data/db:/var/lib/postgresql/data postgres`
10. `./setup_db.sh` to execute the Postgres setup.
11. Copy the saldata.json file into a directory called "saldata". In this example, I created this in my home.
12. `docker run --name "sal-loaddata" --link postgres-sal:db -e ADMIN_PASS=pass -e DB_NAME=sal -e DB_USER=saldbadmin -e DB_PASS=pass -i -t --rm -v /home/nmcspadden/saldata:/saldata -v /usr/local/sal_data/whdimport:/home/docker/sal/whdimport -v /usr/local/sal_data/settings/settings.py:/home/docker/sal/sal/settings.py macadmins/sal /bin/bash`
    * Several things happening in this example. First, we're linking the local "saldata" directory into the container so it can access the Sal dump at /saldata/saldata.json.  
    * Second, we're linking in the 'whdimport' app.  If you are not using this, you can skip this entire -v argument.
    * Third, we're linking in our custom 'settings.py' file. If you didn't make any modifications or add custom apps, you may not need to do this.
    * Make sure your ADMIN_PASS, DB_NAME, DB_USER, and DB_PASS match what you did in setup_db.sh.
    * Last, we're running an interactive shell on this container so we can load the data.

Inside the "sal-loaddata" Docker container:
----
This process sets up Sal to accommodate WHDImport, which introduces extra steps.  If you are not using WHDImport, after #1, skip directly to #7 on this list.

1. `cd /home/docker/sal`
2. `echo "no" | python manage.py syncdb | xargs`
3. `python manage.py migrate`
4. `echo "TRUNCATE django_content_type CASCADE;" | python manage.py dbshell | head -3 | xargs`
5. `python manage.py schemamigration whdimport --auto`
6. `python manage.py migrate whdimport`
7. `python manage.py loaddata /saldata/saldata.json`
8. `exit` when done to remove the container.

Run Sal!
----
Final step:
  `docker run -d --name="sal" -p 80:8000 --link postgres-sal:db -e ADMIN_PASS=pass -e DB_NAME=sal -e DB_USER=saldbadmin -e DB_PASS=pass -v /usr/local/sal_data/whdimport:/home/docker/sal/whdimport -v /usr/local/sal_data/settings/settings.py:/home/docker/sal/sal/settings.py macadmins/sal`
  
Now you can access Sal via your web browser, using your old user account and password, with all existing data migrated.
