"""Dashboard plugin to collate common messages.

This plugin displays a table of messages, sorted by message type, and
counts of their occurance, with links to list views of affected machines.

This plugin takes two configuration settings, set by using the Sal
admin page https://<sal_root>/admin/server/salsetting to add settings.

Settings:
    MessagesPluginThreshold: Integer value. Messages must appear on this
        number of machines (filtered for this view) to appear in the
        plugin.  Defaults to 5.

    MessagesPluginLevel: One of the allowed `Message.MESSAGE_TYPES`
        values. This setting controls which levels of messages are
        considered for display. Messages with the configured level and
        above are displayed. Default is "ERROR".

        e.g. "WARNING" would show messages of WARNING level and above, so
        "WARNING" and "ERROR".

"""
import urllib.parse

from django.db.models import Count

import sal.plugin
from server.models import Message
from server.utils import get_setting


DEFAULT_THRESHOLD = 5


class Messages(sal.plugin.Widget):

    description = 'List of common errors and warnings.'
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        try:
            count_threshold = int(get_setting('MessagesPluginThreshold', DEFAULT_THRESHOLD))
        except ValueError:
            count_threshold = DEFAULT_THRESHOLD

        messages = (
            Message
            .objects
            .filter(machine__in=queryset, message_type__in=self._get_status_levels())
            .values('text', 'message_type')
            .annotate(count=Count('text'))
            .filter(count__gte=count_threshold)
            .order_by('message_type', 'count'))

        context['data'] = messages
        return context

    def filter(self, machines, data):
        unquoted = urllib.parse.unquote(data)
        machines = machines.filter(messages__text=unquoted)
        return machines, f'Machines with message "{unquoted}'

    def _get_status_levels(self):
        message_values = list(zip(*Message.MESSAGE_TYPES))[0]
        # Default to using only the highest severity message.
        status_setting = get_setting('MessagesPluginLevel', message_values[0])
        if status_setting.upper() not in message_values:
            status_setting = message_values[0]

        return message_values[:message_values.index(status_setting) + 1]


