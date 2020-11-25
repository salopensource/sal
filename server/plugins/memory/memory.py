import sal.plugin


GB = 1024 ** 2
MEM_8_GB = 8 * GB
MEM_1575_GB = 15.75 * GB
MEM_16_GB = 16 * GB
TITLES = {
    'ok': 'Machines with more than 16GB memory',
    'warning': 'Machines with between 8GB and 16GB memory',
    'alert': 'Machines with less than 8GB memory'}


class Memory(sal.plugin.Widget):

    description = 'Installed RAM'
    template = 'plugins/traffic_lights.html'

    def get_context(self, machines, **kwargs):
        context = self.super_get_context(machines, **kwargs)
        context['ok_count'] = self._filter(machines, 'ok').count()
        context['ok_label'] = '16GB +'
        context['warning_count'] = self._filter(machines, 'warning').count()
        context['warning_label'] = '8GB +'
        context['alert_count'] = self._filter(machines, 'alert').count()
        context['alert_label'] = '< 8GB'
        return context

    def filter(self, machines, data):
        if data not in TITLES:
            return None, None
        return self._filter(machines, data), TITLES[data]

    def _filter(self, machines, data):
        if data == 'ok':
            machines = machines.filter(memory_kb__gte=MEM_16_GB)
        elif data == 'warning':
            machines = machines.filter(memory_kb__range=[MEM_8_GB, MEM_1575_GB])
        elif data == 'alert':
            machines = machines.filter(memory_kb__lt=MEM_8_GB)
        return machines
