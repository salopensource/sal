API
=====

Sal has a basic API. You will need to create an API key with appropriate permissions. All API endpoints expect three parameters: ``private_key``, ``public_key`` and ``data``. Data should always be a JSON object.

## /api/v1/machines/

``` json
{
  "data":{
        "serials": ["abc123","xyz"]
  }
}
```

To retrieve all machines, do not send ``data``.

## /api/v1/newmachine/

```json
{
  "data":{
        "serial": "abc123",
        "machine_group": "1"
  }
}

``machine_group`` should be the ID of the Machine Group the computer is to be placed into. The serial is the serial number to be added. An error will be returned if either are missing, if the Machine Group doesn't exist or if the serial already exists in Sal.
```
