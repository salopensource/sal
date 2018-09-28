from django.db.models import Count

import sal.plugin


class MachineModels(sal.plugin.Widget):
    description = 'Chart of machine models'
    supported_os_families = [sal.plugin.OSFamilies.darwin, sal.plugin.OSFamilies.windows]

    def get_context(self, machines, **kwargs):
        context = self.super_get_context(machines, **kwargs)
        machines = machines.filter(machine_model__isnull=False).\
            exclude(machine_model='').\
            values('machine_model').\
            annotate(count=Count('machine_model')).\
            order_by('machine_model')

        output = []
        for machine in machines:
            if machine['machine_model']:
                found = False
                nodigits = ''.join(i for i in machine['machine_model'] if i.isalpha())
                machine['machine_model'] = nodigits
                for item in output:
                    if item['machine_model'] == machine['machine_model']:
                        item['count'] = item['count'] + machine['count']
                        found = True
                        break
                # if we get this far, it's not been seen before
                if found is False:
                    output.append(machine)

        context['data'] = output
        return context

    def filter(self, machines, data):
        if data == 'MacBook':
            machines = machines.filter(machine_model__startswith=data).\
                exclude(machine_model__startswith='MacBookPro').\
                exclude(machine_model__startswith='MacBookAir')
        else:
            machines = machines.filter(machine_model__startswith=data)

        return machines, data
