import re
import urllib

from django.db.models import Count, F, Q

from sal.plugin import ReportPlugin


REPORT_Q = Q(pluginscriptsubmission__plugin='MunkiInfo')
REPO_Q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL')
DATA_F = F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')
DATA = 'pluginscript_data'


class MunkiInfo(ReportPlugin):

    class Meta(object):
        description = 'Information on Munki configuration.'
        plugin_type = 'report'
        width = 12

    def get_http_only(self, machines):
        return machines.filter(
            REPORT_Q, REPO_Q,
            pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='http://')

    def get_https_only(self, machines):
        return machines.filter(
            REPORT_Q, REPO_Q,
            pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='https://')

    def get_default_repo(self, machines):
        return machines.filter(
            REPORT_Q, REPO_Q,
            pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='http://munki')

    def get_client_certs(self, machines):
        return machines.filter(
            REPORT_Q,
            pluginscriptsubmission__pluginscriptrow__pluginscript_name='UseClientCertificate',
            pluginscriptsubmission__pluginscriptrow__pluginscript_data='True')

    def get_context(self, machines, group_type=None, group_id=None):
        http_only = self.get_http_only(machines).count()
        https_only = self.get_https_only(machines).count()
        http_munki = self.get_default_repo(machines).count()

        repo_urls = (
            machines
            .filter(REPORT_Q, REPO_Q)
            .annotate(pluginscript_data=DATA_F)
            .values(DATA)
            .annotate(count=Count(DATA))
            .order_by(DATA))

        for url in repo_urls:
            url['item_link'] = 'repo_urls?URL="%s"' % urllib.quote(url[DATA], safe='')

        package_urls = (
            machines
            .filter(
                REPORT_Q,
                pluginscriptsubmission__pluginscriptrow__pluginscript_name='PackageURL')
            .annotate(pluginscript_data=DATA_F)
            .values(DATA)
            .exclude(pluginscript_data='None')
            .annotate(count=Count(DATA))
            .order_by(DATA))

        package_url_prefix = 'package_urls?URL='
        for url in package_urls:
            url['item_link'] = package_url_prefix + urllib.quote(url[DATA])

        manifest_urls = (
            machines
            .filter(
                REPORT_Q,
                pluginscriptsubmission__pluginscriptrow__pluginscript_name='ManifestURL')
            .annotate(pluginscript_data=DATA_F)
            .values(DATA).exclude(pluginscript_data='None')
            .annotate(count=Count(DATA))
            .order_by(DATA))

        manifest_url_prefix = 'manifest_urls?URL='
        for url in manifest_urls:
            url['item_link'] = manifest_url_prefix + urllib.quote(url[DATA])

        catalog_urls = (
            machines
            .filter(
                REPORT_Q,
                pluginscriptsubmission__pluginscriptrow__pluginscript_name='CatalogURL')
            .annotate(pluginscript_data=DATA_F)
            .values(DATA)
            .exclude(pluginscript_data='None')
            .annotate(count=Count(DATA))
            .order_by(DATA))

        catalog_url_prefix = 'catalog_urls?URL='
        for url in catalog_urls:
            url['item_link'] = catalog_url_prefix + urllib.quote(url[DATA])

        client_certs = self.get_client_certs(machines).count()

        context = {
            'http_only': http_only,
            'https_only': https_only,
            'http_munki': http_munki,
            'repo_urls': repo_urls,
            'catalog_urls': catalog_urls,
            'manifest_urls': manifest_urls,
            'package_urls': package_urls,
            'client_certs': client_certs,
            'group_type': group_type,
            'group_id': group_id
        }
        return context

    def filter_machines(self, machines, data):
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

        elif data.startswith('repo_urls?'):
            url_re = re.search(r'repo_urls\?URL=\"(.*)\"', data)
            url = urllib.unquote(url_re.group(1))

            machines = machines.filter(
                REPORT_Q, REPO_Q,
                pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact=url)
            title = 'Machines using %s' % url

        elif data.startswith('manifest_urls?'):
            url_re = re.search(r'manifest_urls\?URL=\"(.*)\"', data)
            url = urllib.unquote(url_re.group(1))

            machines = machines.filter(
                REPORT_Q,
                pluginscriptsubmission__pluginscriptrow__pluginscript_name='ManifestURL',
                pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact=url)
            title = 'Machines using %s' % url

        return machines, title
