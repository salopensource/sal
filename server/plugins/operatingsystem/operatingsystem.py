from distutils.version import LooseVersion

from django.db.models import Count

# from sal.plugin import MachinesPlugin
import sal.plugin


class OperatingSystem(sal.plugin.MachinesPlugin):

    description = 'List of operating system versions'
    template = 'operatingsystem/templates/operatingsystem.html'

    def get_context(self, machines, **kwargs):
        # Remove invalid versions, then count and sort the results.
        os_info = (
            machines
            .exclude(operating_system__isnull=True)
            .exclude(operating_system__exact='')
            .values('operating_system', 'os_family')
            .annotate(count=Count('operating_system'))
            .order_by('os_family', 'operating_system'))

        mac_os_info = []
        windows_os_info = []
        linux_os_info = []
        chrome_os_info = []

        for machine in os_info:
            if machine['os_family'] == 'Darwin':
                mac_os_info.append(machine)
            elif machine['os_family'] == 'Windows':
                windows_os_info.append(machine)
            elif machine['os_family'] == 'Linux':
                linux_os_info.append(machine)
            elif machine['os_family'] == 'ChromeOS':
                chrome_os_info.append(machine)

        # you and your lanbda's @sheacraig...
        os_key = lambda x: LooseVersion(x["operating_system"])  # noqa: E731

        mac_os_info = sorted(mac_os_info, key=os_key, reverse=True)
        windows_os_info = sorted(windows_os_info, key=os_key, reverse=True)
        linux_os_info = sorted(linux_os_info, key=os_key, reverse=True)
        chrome_os_info = sorted(chrome_os_info, key=os_key, reverse=True)

        context = {
            'title': 'Operating Systems',
            'mac_data': mac_os_info,
            'windows_data': windows_os_info,
            'linux_data': linux_os_info,
            'chrome_data': chrome_os_info,
            'group_type': kwargs['group_type'],
            'group_id': kwargs['group_id']}
        return context

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform
        # some filtering based on the 'data' part of the url from the
        # show_widget output. Just return your filtered list of machines and
        # the page title.

        machines = machines.filter(operating_system__exact=data)

        return machines, 'Machines running ' + data
