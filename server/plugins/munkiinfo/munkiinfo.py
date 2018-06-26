import re
import urllib

from django.db.models import Count, F, Q
from django.http import Http404

import sal.plugin


REPORT_Q = Q(pluginscriptsubmission__plugin='MunkiInfo')
DATA_F = F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')
DATA = 'pluginscript_data'
URLS = ('SoftwareRepo', 'Package', 'Manifest', 'Catalog')
URL_QS = {k: Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name=k + 'URL') for k in URLS}


class MunkiInfo(sal.plugin.ReportPlugin):

    description = 'Information on Munki configuration.'

    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_http_only(self, machines):
        return machines.filter(
            REPORT_Q, URL_QS['SoftwareRepo'],
            pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='http://')

    def get_https_only(self, machines):
        return machines.filter(
            REPORT_Q, URL_QS['SoftwareRepo'],
            pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='https://')

    def get_default_repo(self, machines):
        return machines.filter(
            REPORT_Q, URL_QS['SoftwareRepo'],
            pluginscriptsubmission__pluginscriptrow__pluginscript_data='http://munki')

    def get_client_certs(self, machines):
        return machines.filter(
            REPORT_Q,
            pluginscriptsubmission__pluginscriptrow__pluginscript_name='UseClientCertificate',
            pluginscriptsubmission__pluginscriptrow__pluginscript_data='True')

    def get_context(self, machines, group_type=None, group_id=None):
        context = self.super_get_context(machines, group_type=group_type, group_id=group_id)

        context['http_only'] = self.get_http_only(machines).count()
        context['https_only'] = self.get_https_only(machines).count()
        context['http_munki'] = self.get_default_repo(machines).count()
        context['client_certs'] = self.get_client_certs(machines).count()
        context.update(
            {k: self.process_urls(machines, (REPORT_Q, URL_QS[k]), k + '?URL=') for k in URLS})

        return context

    def filter(self, machines, data):
        if data.startswith('http_only?'):
            machines = self.get_http_only(machines)
            title = 'Machines using HTTP'

        elif data.startswith('https_only?'):
            machines = self.get_https_only(machines)
            title = 'Machines using HTTPS'

        elif data.startswith('http_munki?'):
            machines = self.get_default_repo(machines)
            title = 'Machines connecting to Munki using http://munki'

        elif data.startswith('client_certs?'):
            machines = self.get_client_certs(machines)
            title = 'Machines connecting to Munki using client certificates'

        elif any(data.split('?')[0] == k for k in URLS):
            url_re = re.search(r'(.*)\?URL=\"(.*)\"', data)
            try:
                key = url_re.group(1)
                url = urllib.unquote(url_re.group(2))
            except IndexError:
                raise Http404

            machines = machines.filter(
                REPORT_Q,
                URL_QS[key],
                pluginscriptsubmission__pluginscriptrow__pluginscript_data=url)
            title = 'Machines using %s %s' % (key, url)

        else:
            return None, None

        return machines, title

    def process_urls(self, queryset, filters, prefix):
        processed = (
            queryset
            .filter(*filters)
            .annotate(pluginscript_data=DATA_F)
            .values(DATA)
            .exclude(pluginscript_data='None')
            .annotate(count=Count(DATA))
            .order_by(DATA))

        for url in processed:
            url['item_link'] = '{}"{}"'.format(prefix, urllib.quote(url[DATA], safe=''))

        return processed
