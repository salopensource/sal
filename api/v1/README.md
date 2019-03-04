# Version 1 Sal API
This version of the Sal API is now deprecated and will be removed in an
upcoming major version update. Please transition to the v2 API.

In general, the changes made to v2 of the API are as follows:

## General
- Enabled the Django Rest Framework (DRF) documentation site (`sal_url.com/api/docs`).
- Fixed the API authentication setup to allow session sign in to the docs site. Basically, this means you log in with your Django user (whomever you use to sign into the Sal main site) to be able to use the docs site to make interactive requests.
- Move all view-class level permissions and auth code to global settings in `system_settings.py`
- Move all API endpoints to DRF `ModelViewSet` or `ReadOnlyModelViewSet` instances. This greatly automates the mostly boilerplate setup of all endpoints, as well as enables extra features we didn't have before (filtering).
    - Despite documentation to the contrary, `ordering` does not seem to work as a querystring.

## Endpoint Changes
- Most endpoints now use the filter querystring `?filter=<something>` to filter results. The documentation page lists all available filters for each endpoint.
    - The column names are exactly as they are in the python code. In some places, this added flexibility means longer names, the prime example being that in the past, several endpoints expected a mandatory serial parameter. This has been moved to being a filter where it makes sense, but due to the relations between models, may need to be expressed as `?filter=machine__serial` (using the django filter dunder notation to follow relationships).
- Removed `plugin_script_submissions` and just nested them in `plugin_script_rows`
- `pending_updates` and `pending_apple_updates` now allow you to list all rows of data, and use the standard filtering querystrings to filter by machine serial. This means you may also filter by machine hostname, as well as perform a text search using the `?search=` querystring.
`/api/search` removed: This endpoint allowed you to perform a text search for machines. Since this can be done with the `/api/machines/?search=<something>` endpoint, `/api/search` has been removed.
- `/api/search/<id>` originally returned the results of a SavedSearch. It has been removed in favor of...
- `/api/saved_searches`  Now it operates like the other endpoints and returns a list of SavedSearch objects. or an individual saved search with the <id> parameter.
    - You can execute a search through the additional endpoint `/api/search/<id>/execute`. This also uses the `?full` query parameter to control whether you want all `Machine` fields. It defaults to only returning `id`, `serial`, `console_user`, and `last_checkin`. (This is how the Search module is currently coded).
- `/api/machines` grows an extensive list of filter fields, and search capabilities. Basically, all text-based fields on `Machine` are searched when using the `/api/machines/?search=tacos` querystring.
- `/api/machines`Using the `?fields` or `?fields!` querystring, you can customize the fields you want the API to return or exclude. Full documentation is added into the docs site.

There is a slight discrepancy in that the results of the `/search/views.py` `search_machines()` function uses an even more abbreviated Machine record than the `/api/machines` endpoint when called with argument `full=False`. The fields are currently hardcoded into an overridden `Serializer` to handle this currently. If the search results ever change, this hardcoded field specification would have to change as well.