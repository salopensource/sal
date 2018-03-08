import sal.plugin


GB = 1024 ** 2
MEM_4_GB = 4 * GB
MEM_775_GB = 7.75 * GB
MEM_8_GB = 8 * GB
TITLES = {
    'ok': 'Machines with more than 8GB memory',
    'warning': 'Machines with between 4GB and 8GB memory',
    'alert': 'Machines with less than 4GB memory'}


class Memory(sal.plugin.MachinesPlugin):

    description = 'Installed RAM'
    template = 'plugins/traffic_lights.html'

    def get_context(self, machines, **kwargs):
        context = self.super_context(machines, **kwargs)
        context['ok_count'] = self._filter(machines, 'ok').count()
        context['ok_label'] = '8GB +'
        context['warning_count'] = self._filter(machines, 'warning').count()
        context['warning_label'] = '4GB +'
        context['alert_count'] = self._filter(machines, 'alert').count()
        context['alert_label'] = '< 4GB'
        return context

    def filter(self, machines, data):
        return self._filter(machines, data), TITLES[data]

    def _filter(self, machines, data):
        if data == 'ok':
            machines = machines.filter(memory_kb__gte=MEM_8_GB)
        elif data == 'warning':
            machines = machines.filter(memory_kb__range=[MEM_4_GB, MEM_775_GB])
        elif data == 'alert':
            machines = machines.filter(memory_kb__lt=MEM_4_GB)
        return machines
