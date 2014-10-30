Running Sal on Docker
================

This guide assumes you have installed Docker as per the [instructions on their site](https://docs.docker.com/installation/#installation), and that you have a working knowledge of the basics of Docker. The [Docker user guide](https://docs.docker.com/userguide/) is an excellent place to start.

## Basic setup

This will get you going with a default Sal installation, with a Postgres database. All commands below should be run as root.

### Database

``` bash
# This is where the database data will live. Adjust to your taste
$ mkdir -p /usr/local/sal_data/db
$ docker pull postgres:9.4
$ docker run --name="postgres-sal" -d -v /usr/local/sal_data/db:/var/lib/postgresql/data postgres
$ bash <(curl -s https://raw.githubusercontent.com/macadmins/sal/master/setup_db.sh)
```

If you want to change the default database admin username and password, download the ``setup_db.sh`` script and run it manually.

### Running Sal

Assuming you've not changed the default database username and password:

``` bash
$ docker run -d --name="sal"\
  -p 80:8000 \
  --link postgres-sal:db \
  -e ADMIN_PASS=pass \
  -e DB_NAME=sal \
  -e DB_USER=admin \
  -e DB_PASS=password \
  macadmins/sal
  ```
  
This will allow you to log in with the username ``admin`` and the password ``pass`` (which I suggest you change!).

### Upgrading

Upgrading using Docker is simple:

``` bash
$ docker pull macadmins/sal  
$ docker stop sal  
$ docker rm sal  
$ docker run -d --name="sal"\
  -p 80:8000 \
  --link postgres-sal:db \
  -e ADMIN_PASS=pass \
  -e DB_NAME=sal \
  -e DB_USER=admin \
  -e DB_PASS=password \
  macadmins/sal
  ```
