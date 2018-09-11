from collections import defaultdict, OrderedDict
from distutils.version import LooseVersion

from django.db.models import Count

import sal.plugin

from server.utils import get_setting


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

        # print grouped
        normalize_chromeos_versions = get_setting('normalize_chromeos_versions')
        # print type(normalize_chromeos_versions)
        if normalize_chromeos_versions:
            chrome_items = []
            for chrome_item in grouped['Chrome OS']:
                version_array = chrome_item['operating_system'].split('.')
                if len(version_array) <= 3:
                    version_string = chrome_item['operating_system']
                else:
                    version_string = '{}.{}.{}'.format(
                        version_array[0],
                        version_array[1],
                        version_array[2]
                    )
                found = False

                for item in chrome_items:
                    if item['operating_system'] == version_string:
                        item['count'] = item['count'] + chrome_item['count']
                        found = True
                        continue
                if not found:
                    item_to_add = {}
                    item_to_add['operating_system'] = version_string
                    item_to_add['count'] = chrome_item['count']
                    chrome_items.append(item_to_add)
                
            grouped['Chrome OS'] = chrome_items
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

        normalize_chromeos_versions = get_setting('normalize_chromeos_versions')
        if os_family == 'ChromeOS' and normalize_chromeos_versions:
            machines = machines.filter(
                operating_system__starts_with=operating_system,
                os_family=os_family
            )
        else:
            machines = machines.filter(operating_system=operating_system, os_family=os_family)
        return machines, 'Machines running {} {}'.format(OS_TABLE[os_family], operating_system)
