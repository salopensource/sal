# Troubleshooting

## Enabling debug mode

There is a very verbose debug mode built into Sal. To enable it when using Docker, add the following to your startup command:

```
-e DOCKER_SAL_DEBUG=true
```

If you are using the legacy method, add the following to ``sal/settings.py``:

``` python
DEBUG = True
```

This will cause any application error to throw up a detailled error (which will be returned by the preflight and postflight scripts if the error is on the client end). If you don't understand the error, post the full error to the [Google Group](http://groups.google.com/group/sal-discuss).