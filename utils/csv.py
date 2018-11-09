"""CSV utilites"""


import csv
import io
import itertools
from typing import List, Dict, Any

from django.db.models.query import QuerySet
from django.http import StreamingHttpResponse

import server.models
import server.text_utils
import server.utils


IGNORED_CSV_FIELDS = ('id', 'machine_group', 'report')
MACHINE_FIELDS = [
    field.name for field in server.models.Machine._meta.get_fields()
    if not field.is_relation and field.name not in IGNORED_CSV_FIELDS]


class PassthroughIO(io.StringIO):
    """Implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def row_helper(item, fields: Dict) -> List[Any]:
    """Given a dict of fields, extract an output tuple

    The fields dict should be formed with:
        key: Output name
        value: Dot notated reference to attribute to extract.
    """
    row = []
    for name, reference in fields.items():
        if not reference:
            row.append(getattr(item, name))
        else:
            obj = item
            for sub_field in reference.split('.'):
                obj = getattr(obj, sub_field)
            row.append(obj)
    return row


def machine_fields():
    machine_fields = {
        field.name: None for field in server.models.Machine._meta.get_fields()
        if not field.is_relation and field.name not in IGNORED_CSV_FIELDS}
    machine_fields['business unit'] = 'machine_group.business_unit.name'
    machine_fields['machine group'] = 'machine_group.name'
    return machine_fields


def get_csv_response(queryset: QuerySet,
                     fields: dict,
                     title: str) -> StreamingHttpResponse:
    writer = csv.writer(PassthroughIO())

    # Nest field names into an iterable of 1 so it can be chained.
    # Add in our two foreign key traversals by name.
    headers = [fields.keys()]
    data = (row_helper(item, fields) for item in queryset)
    # Chain the headers and the data into a single iterator.
    generator = (writer.writerow(row) for row in itertools.chain(headers, data))

    # Streaming responses require a generator; which is good, as it can
    # process machines one by one rather than shoving the entire output
    # into memory.
    response = StreamingHttpResponse(generator, content_type="text/csv")
    # If DEBUG_CSV  is enabled, just print output rather than download.
    if not server.utils.get_django_setting('DEBUG_CSV', False):
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title
    return response
