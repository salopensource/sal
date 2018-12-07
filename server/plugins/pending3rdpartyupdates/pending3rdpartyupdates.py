from distutils.version import LooseVersion

from django.db.models import Count
from django.shortcuts import get_object_or_404

import sal.plugin
from server.models import InstalledUpdate


class Pending3rdPartyUpdates(sal.plugin.Widget):

    description = 'List of pending third party updates'
    template = 'plugins/pendingupdates.html'
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        updates = (
            InstalledUpdate.objects
            .filter(machine__in=queryset, installed=False)
            .values('update', 'update_version', 'display_name')
            .annotate(count=Count('update')))

        # Sort first by version number, then name.
        # Some updates don't have a version number and show up as just
        # whitespace, so we have to treat them as a 0.0 version.
        updates = sorted(updates, key=version_sort, reverse=True)
        context['data'] = sorted(updates, key=lambda x: x['display_name'])
        return context

    def filter(self, machines, data):
        try:
            (update_name, update_version) = data.split("--")
        except ValueError:
            return None, None

        machines = machines.filter(installed_updates__update=update_name,
                                   installed_updates__update_version=update_version,
                                   installed_updates__installed=False)

        # get the display name of the update
        try:
            display_name = (
                InstalledUpdate.objects
                .filter(update=update_name, update_version=update_version, installed=False)
                .values('display_name')
                .first())['display_name']
        except (AttributeError, TypeError):
            # Nothing was found
            return None, None

        return machines, 'Machines that need to install {} {}'.format(display_name, update_version)


def version_sort(i):
    return LooseVersion(i['update_version'].strip() or '0.0')
