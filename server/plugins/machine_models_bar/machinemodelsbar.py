#!/usr/bin/python


from collections import Counter

from yapsy.IPlugin import IPlugin

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


class MachineModelsBar(IPlugin):
    name = "MachineModelsBar"

    def widget_width(self):
        return 12

    def plugin_type(self):
        return "builtin"

    def get_description(self):
        return "Machine Models"

    def widget_content(self, page, machines=None, theid=None):
        if page == "front":
            t = loader.get_template(
                "machine_models_bar/templates/front.html")
        elif page in ("bu_dashboard", "group_dashboard"):
            t = loader.get_template(
                "machine_models_bar/templates/id.html")

        # TODO: This works around the potential for Sal to not be able
        # to grab the friendly model name from Apple at inventory time.
        # Eventually this situation will be corrected by using a cached
        # lookup table.
        model_conversion = {
            machine.machine_model: machine.machine_model_friendly
            for machine in machines if machine.machine_model_friendly}
        machine_models = Counter()
        for machine in machines:
            if machine.machine_model_friendly:
                machine_model_friendly = machine.machine_model_friendly
            else:
                machine_model_friendly = model_conversion.get(
                    machine.machine_model, machine.machine_model)
            machine_models[machine_model_friendly] += 1

        data = [{"label": model, "value": machine_models[model]}
                for model in machine_models]
        sorted_data = sorted(data, key=lambda x: x["value"])

        c = Context({
            "title": "Hardware Models",
            "data": sorted_data,
            "theid": theid,
            "page": page})

        return t.render(c)

    def filter_machines(self, machines, data):
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
