from collections import Counter
from operator import itemgetter

from django.db.models import Q

import sal.plugin
from server.models import *


class MachineModelsBar(sal.plugin.MachinesPlugin):

    description = "Machine Models"
    widget_width = 12

    def get_context(self, queryset, **kwargs):
        context = self.super_context(queryset, **kwargs)
        # TODO: This works around the potential for Sal to not be able
        # to grab the friendly model name from Apple at inventory time.
        # Eventually this situation will be corrected by using a cached
        # lookup table.
        model_conversion = {
            machine.machine_model: machine.machine_model_friendly
            for machine in queryset if machine.machine_model_friendly}
        machine_models = Counter()
        for machine in queryset:
            if machine.machine_model_friendly:
                machine_model_friendly = machine.machine_model_friendly
            else:
                machine_model_friendly = model_conversion.get(
                    machine.machine_model, machine.machine_model)
            machine_models[machine_model_friendly] += 1

        data = [{"label": model, "value": machine_models[model]}
                for model in machine_models]
        sorted_data = sorted(data, key=itemgetter("value"))

        context["data"] = sorted_data

        return context

    def filter(self, machines, data):
        # TODO: See above.
        model_conversion = {
            machine.machine_model_friendly: machine.machine_model
            for machine in machines if machine.machine_model_friendly}
        machines = machines.filter(
            Q(machine_model_friendly=data) |
            Q(machine_model=model_conversion.get(data, data),
              machine_model_friendly=None))
        title = "All machines with model: {}".format(data)

        return machines, title
