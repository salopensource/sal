"""
Query fields for Django Rest Framework, based mostly on
https://github.com/wimglenn/djangorestframework-queryfields

This is a serializer mixin to allow query strings to your API calls to
exclude/include fields.

The modifications here are to add in a special "simple_fields" class attribute.
Serializers may specify the `simple_fields` which are the subset of
fields to include when serving simple requests.
"""


from server.models import *


class QueryFieldsMixin(object):

    # If using Django filters in the API, these labels mustn't conflict with
    # any model field names.
    include_arg_name = 'fields'
    exclude_arg_name = 'fields!'

    simple_fields = None

    # Split field names by this string.  It doesn't necessarily have to be a
    # single character.  Avoid RFC 1738 reserved characters i.e. ';', '/', '?',
    # ':', '@', '=' and '&'
    delimiter = ','

    def __init__(self, *args, **kwargs):
        super(QueryFieldsMixin, self).__init__(*args, **kwargs)

        try:
            request = self.context['request']
            method = request.method
        except (AttributeError, TypeError, KeyError):
            # The serializer was not initialized with request context.
            return

        if method != 'GET':
            return

        try:
            query_params = request.query_params
        except AttributeError:
            # DRF 2
            query_params = getattr(request, 'QUERY_PARAMS', request.GET)

        includes = query_params.getlist(self.include_arg_name)
        include_field_names = {
            name for names in includes for name in names.split(self.delimiter)
            if name}

        excludes = query_params.getlist(self.exclude_arg_name)
        exclude_field_names = {
            name for names in excludes for name in names.split(self.delimiter)
            if name}

        if 'full' not in query_params and self.simple_fields:
            include_field_names.update(self.simple_fields)

        if not include_field_names and not exclude_field_names:
            # No user fields filtering was requested, we have nothing to do
            # here.
            return

        serializer_field_names = set(self.fields)

        fields_to_drop = serializer_field_names & exclude_field_names
        if include_field_names:
            fields_to_drop |= serializer_field_names - include_field_names

        for field in fields_to_drop:
            self.fields.pop(field)
