Running Sal on Docker
================

This guide assumes you have installed Docker as per the [instructions on their site](https://docs.docker.com/installation/#installation), and that you have a working knowledge of the basics of Docker. The [Docker user guide](https://docs.docker.com/userguide/) is an excellent place to start.

## Basic setup

This will get you going with a default Sal installation, with a Postgres database. All commands below should be run as root.

### Database

``` bash
# This is where the database data will live. Adjust to your taste
$ mkdir -p /usr/local/sal_data/db
$ docker run -d --name="postgres-sal" \
  -v /usr/local/sal_data/db:/var/lib/postgresql/data \
  -e DB_NAME=sal \
  -e DB_USER=admin \
  -e DB_PASS=password \
  --restart="always" \
  grahamgilbert/postgres
```

Set the database details according to your preferences.

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
  macadmins/sal:2.3.1.1
  ```

This will allow you to log in with the username ``admin`` and the password ``pass`` (which I suggest you change!).

### Upgrading

Upgrading using Docker is simple:

``` bash
$ docker pull macadmins/sal  
$ docker stop sal  
$ docker rm sal  
$ docker run -d --name="sal" \
  -p 80:8000 \
  --link postgres-sal:db \
  -e ADMIN_PASS=pass \
  -e DB_NAME=sal \
  -e DB_USER=admin \
  -e DB_PASS=password \
  macadmins/sal:2.3.1.1
  ```

### Other options and plugins

For other options that can be set via environment variables, and for how to use advanced options such as plugins, see the [repo on the Docker Hub](https://registry.hub.docker.com/u/macadmins/sal/).
