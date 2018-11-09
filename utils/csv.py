"""CSV utilites"""


import csv
import io
import itertools

import server.models
import server.text_utils
import server.utils

from django.http import StreamingHttpResponse


IGNORED_CSV_FIELDS = ('id', 'machine_group', 'report')
MACHINE_FIELDS = [
    field.name for field in server.models.Machine._meta.get_fields()
    if not field.is_relation and field.name not in IGNORED_CSV_FIELDS]


class PassthroughIO(io.StringIO):
    """Implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def machine_row(machine):
    rows = (getattr(machine, field) for field in MACHINE_FIELDS)
    # Manually add in foreign key traversals to BU and MG names.
    group_names = [machine.machine_group.business_unit.name, machine.machine_group.name]
    return itertools.chain(rows, group_names)


def get_csv_response(machines, title):
    writer = csv.writer(PassthroughIO())

    # Nest field names into an iterable of 1 so it can be chained.
    # Add in our two foreign key traversals by name.
    headers = [MACHINE_FIELDS + ['Business Unit', 'Machine Group']]
    data = (machine_row(machine) for machine in machines)
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
