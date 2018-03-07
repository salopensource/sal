import sal.plugin


TITLES = {'ok': 'Machines with less than 80% disk utilization',
          'warning': 'Machines with 80%-90% disk utilization',
          'alert': 'Machines with more than 90% disk utilization'}


class DiskSpace(sal.plugin.MachinesPlugin):

    description = 'Available disk space'
    template = 'plugins/traffic_lights.html'

    def get_context(self, machines, **kwargs):
        context = self.super_context(machines, **kwargs)
        context['ok_label'] = '< 80%'
        context['ok_count'] = self.filter_by_diskspace(machines, 'ok').count()
        context['warning_label'] = '80% +'
        context['warning_count'] = self.filter_by_diskspace(machines, 'warning').count()
        context['alert_label'] = '90% +'
        context['alert_count'] = self.filter_by_diskspace(machines, 'alert').count()
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
