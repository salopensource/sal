from yapsy.IPlugin import IPlugin

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


class MunkiVersion(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Chart of installed versions of Munki'

    def widget_content(self, page, machines=None, theid=None):
        if page == 'front':
            t = loader.get_template('munkiversion/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('munkiversion/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('munkiversion/templates/id.html')

        try:
            munki_info = machines.values('munki_version').annotate(
                count=Count('munki_version')).order_by('munki_version')
        except Exception:
            munki_info = []

        c = Context({
            'title': 'Munki Version',
            'data': munki_info,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):

        machines = machines.filter(munki_version__exact=data)

        title = 'Machines running version {} of MSC'.format(data)
        return machines, title
