import sal.plugin


TITLES = {'ok': 'Machines with less than 80% disk utilization',
          'warning': 'Machines with 80%-90% disk utilization',
          'alert': 'Machines with more than 90% disk utilization'}


class DiskSpace(sal.plugin.MachinesPlugin):

    description = 'Available disk space'
    template = 'plugins/traffic_lights.html'

    def get_context(self, machines, **kwargs):
        disk_ok = self.filter_by_diskspace(machines, 'ok').count()
        disk_warning = self.filter_by_diskspace(machines, 'warning').count()
        disk_alert = self.filter_by_diskspace(machines, 'alert').count()

        context = {
            'title': 'Disk Space',
            'ok_label': '< 80%',
            'ok_count': disk_ok,
            'warning_label': '80% +',
            'warning_count': disk_warning,
            'alert_label': '90% +',
            'alert_count': disk_alert,
            'plugin': 'DiskSpace',
            'group_id': kwargs['group_id'],
            'group_type': kwargs['group_type']}
        return context

    def filter(self, machines, data):
        title = TITLES[data]
        machines = self.filter_by_diskspace(machines, data)
        return machines, title

    def filter_by_diskspace(self, machines, data):
        if data == 'ok':
            machines = machines.filter(hd_percent__lt=80)
        elif data == 'warning':
            machines = machines.filter(hd_percent__range=["80", "89"])
        elif data == 'alert':
            machines = machines.filter(hd_percent__gte=90)
        else:
            machines = None

        return machines
