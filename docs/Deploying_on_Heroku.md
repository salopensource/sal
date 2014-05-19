This was originally published at [http://grahamgilbert.com/blog/2014/05/19/deploying-sal-on-heroku/](http://grahamgilbert.com/blog/2014/05/19/deploying-sal-on-heroku/).

Setting up everything you need for Sal can be difficult, especially if you only have an OS X server available. Thankfully, Sal is built on top of a very common Python framework, Django. And even more thankfully, you can run Django on a whole host of [PaaS](http://en.wikipedia.org/wiki/Platform_as_a_service) providers, including [Heroku](https://www.heroku.com).

Heroku has a very generous [free tier](https://www.heroku.com/pricing) that will easily handle a small Sal installation, so let's get started.

## Heroku toolkit

If you've never used Heroku before, you're going to need to head over to [their site](http://heroku.com) and sign up for a free account. Whilst you're there, you're also going to need to install their toolbelt. [Grab the package](http://toolbelt.herokuapp.com/) and follow their instructions for linking it to your account.

## Configure

Now we need to get a copy of Sal and configure it. Assuming you keep your code in ~/src:

``` bash
$ cd ~/src
$ git clone https://github.com/grahamgilbert/sal
$ cd sal
```

Now we need to make a copy of sal/example_settings.py

``` bash
$ cp sal/example_settings.py sal/settings.py
```

And edit sal/settings.py in your favourite editor to your liking (probably time zone at least).

Heroku uses git for deployment, so we need to commit our changes.

``` bash
$ git add .
$ git commit -m "initial commit to heroku"
```

We're nearly there! Time to create our environment on Heroku

``` bash
$ heroku create
```

Of course we haven't pushed Sal to Heroku yet. Let's fix that.

``` bash
$ git push heroku master
```

You'll see Sal being pushed up to Heroku and Sal's requirements being installed. A Postgres database will also automatically be created for you. The database will be empty though, so let's populate it with what we need.

``` bash
$ heroku run python manage.py syncdb
```

When asked, you certainly *do* want to create a super user. Use a strong username and password as this is the admin for your Sal application.

One last command to run:

``` bash
$ heroku run python manage.py migrate
```

Your Sal installation is ready to use:

``` bash
$ heroku open
```

As said earlier, the free version does have some limits. The most important with Sal is the number of rows you can have in the free database (10,000), so the more information you collect from each machine (Facter Facts and Munki Conditions), the larger your database is. It's a measley $9 a month to upgrade your database to 10 million rows, so it's easy to scale your database. For more information on upgrading your Heroku environment see [their documentation](https://devcenter.heroku.com/articles/upgrade-heroku-postgres-with-pgbackups).