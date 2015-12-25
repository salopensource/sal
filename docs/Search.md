## Search

Sal has full search across machines, Facts and Munki conditions. If you want to search on Machine info, enter your search terms without anything extra, otherwise, enter a search prefix followed by your search terms. For example: `inventory: Microsoft Excel`

| Search Type | Prefix |
|-------------|--------|
| Machine info | |
| Munki conditions | `condition:` |
| Facter facts | `facter:` |
| Application inventory | `inventory:` |

## Indexing

Sal will index new items when they are added or updated, but if you wish to index your items manually:

### Docker

``` bash
$ docker exec -ti sal bash
$ python /home/docker/sal/manage.py buildwatson
```

### Legacy setup (Apache)

``` bash
$ su saluser
$ bash
$ source /usr/local/sal_env/bin/activate
$ python /usr/local/sal_env/sal/manage.py buildwatson
```
