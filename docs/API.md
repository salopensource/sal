API
=====

Sal has a basic REST API. You will need to create an API key before using it. You should send your private key and public key as headers (``publickey`` and ``privatekey``).

## Machines

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/machines
```

Will retrieve all machines.

To retrieve a single machine:

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/machines/MACHINESERIALNUMBER
```

To create a machine, you will need to send a JSON object as the POST data. You can use any key that can be retrieved from the API *except*:

* Facts
* Conditions
* Pending Apple Updates
* Pending 3rd Party Updates

You **must** set machine_group to the ID of the Machine Group the computer is to be placed into.

You can delete a machine by sending a ``DELETE`` command with your request (please see [this guide](http://blogs.plexibus.com/2009/01/15/rest-esting-with-curl/) on using REST APIs if that doesn't make sense!)

## Facts

You can retrieve all facts for a machine:


``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/facts/MACHINESERIALNUMBER
```

## Munki Conditions

To retrieve all Munki Conditions for a machine:

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/conditions/MACHINESERIALNUMBER
```

## Machine Groups

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/machine_groups
```

Will retrieve all machine groups.

To retrieve a single machine group:

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/machine_groups/MACHINEGROUPID
```

To create a Machine Group, you will need to send a JSON object as the POST data. You can use any key that can be retrieved from the API.

You **must** set business_unit to the ID of the Business Unit the Machine Group is to be placed into.

You can delete a machine group by sending a ``DELETE`` command with your request.

## Business Units

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/business_units
```

Will retrieve all Business Units.

To retrieve a single Business Unit:

``` bash
$ curl -H "privatekey:YOURPRIVATEKEY" -H "publickey:YOURPUBLICKEY" http://sal/api/business_units/BUSINESSUNITID
```

To create a Business Unit, you will need to send a JSON object as the POST data. You can use any key that can be retrieved from the API.

You can delete a Business Unit by sending a ``DELETE`` command with your request.
