from yapsy.IPlugin import IPlugin

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


class Sip(IPlugin):
    def widget_width(self):
        return 4

    def plugin_type(self):
        return 'builtin'

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('sip/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('sip/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('sip/templates/id.html')

        try:
            ok = machines.filter(pluginscriptsubmission__plugin__exact='Sip', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='SIP', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled').count()  # noqa: E501
        except Exception:
            ok = 0

        try:
            alert = machines.filter(pluginscriptsubmission__plugin__exact='Sip', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='SIP', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').count()  # noqa: E501
        except Exception:
            alert = 0

        c = Context({
            'title': 'SIP',
            'ok_count': ok,
            'alert_count': alert,
            'plugin': 'Sip',
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'ok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Sip', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='SIP', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled')  # noqa: E501
            title = 'Machines with Sip enabled'

        elif data == 'alert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Sip', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='SIP', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled')  # noqa: E501
            title = 'Machines without SIP enabled'

        else:
            machines = None
            title = None

        return machines, title
