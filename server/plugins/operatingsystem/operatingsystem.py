from collections import defaultdict, OrderedDict
from distutils.version import LooseVersion

from django.db.models import Count

import sal.plugin


# This table is also used for sequnecing output, so use OrderedDict.
OS_TABLE = OrderedDict(Darwin='macOS', Windows='Windows', Linux='Linux', ChromeOS='Chrome OS')


class OperatingSystem(sal.plugin.Widget):

    description = 'List of operating system versions'
    template = 'operatingsystem/templates/operatingsystem.html'

    def get_context(self, machines, **kwargs):
        context = self.super_get_context(machines, **kwargs)
        # Remove invalid versions, then annotate with a count.
        os_info = (
            machines
            .exclude(operating_system__isnull=True)
            .exclude(operating_system='')
            .order_by('operating_system')
            .values('operating_system', 'os_family')
            .distinct()
            .annotate(count=Count('operating_system')))

        grouped = defaultdict(list)
        for version in os_info:
            os_type = OS_TABLE[version['os_family']]
            grouped[os_type].append(version)

        # you and your lanbda's @sheacraig...
        os_key = lambda x: LooseVersion(x["operating_system"])  # noqa: E731
        output = [
            (key, sorted(grouped[key], key=os_key, reverse=True)) for key in OS_TABLE.values()]
        context['os_info'] = output

        return context

    def filter(self, machines, data):
        try:
            os_family, operating_system = data.split('&')
        except ValueError:
            return None, None
        machines = machines.filter(operating_system=operating_system, os_family=os_family)
        return machines, 'Machines running {} {}'.format(OS_TABLE[os_family], operating_system)
