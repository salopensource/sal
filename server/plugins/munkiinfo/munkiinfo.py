from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count, F
from server.models import *
from catalog.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
import plistlib
import urllib
import re

class MunkiInfo(IPlugin):
    def plugin_type(self):
        return 'report'

    def widget_width(self):
        return 12

    def get_description(self):
        return 'Information on Munki configuration.'

    def get_title(self):
        return 'Munki'

    def safe_unicode(self, s):
        if isinstance(s, unicode):
            return s.encode('utf-8', errors='replace')
        else:
            return s

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('munkiinfo/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('munkiinfo/templates/front.html')

        if page == 'group_dashboard':
            t = loader.get_template('munkiinfo/templates/front.html')

        # HTTP only machines
        http_only = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='http://').count()

        # HTTPS only machines
        https_only = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='https://').count()

        # Distinct Repo URLs
        repo_urls = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL').annotate(pluginscript_data=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')).values('pluginscript_data').annotate(count=Count('pluginscript_data')).order_by('pluginscript_data')

        for url in repo_urls:
            url['item_link'] = 'repo_urls?URL="%s"' % urllib.quote(url['pluginscript_data'],
            safe='')

        # Distinct Package URLs
        try:
            package_urls = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='PackageURL').annotate(pluginscript_data=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')).values('pluginscript_data').exclude(pluginscript_data='None').annotate(count=Count('pluginscript_data')).order_by('pluginscript_data')
            package_url_prefix = 'package_urls?URL='
            for url in package_urls:
                url['item_link'] = package_url_prefix + urllib.quote(url['pluginscript_data'])
        except:
            package_urls = None


        # Distinct Manifest URLs
        try:
            manifest_urls = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='ManifestURL').annotate(pluginscript_data=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')).values('pluginscript_data').exclude(pluginscript_data='None').annotate(count=Count('pluginscript_data')).order_by('pluginscript_data')
            manifest_url_prefix = 'manifest_urls?URL='
            for url in manifest_urls:
                url['item_link'] = manifest_url_prefix + urllib.quote(url['pluginscript_data'])

        except:
            manifest_urls = None

        # Distinct Catalog URLs
        try:
            catalog_urls = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='CatalogURL').annotate(pluginscript_data=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')).values('pluginscript_data').exclude(pluginscript_data='None').annotate(count=Count('pluginscript_data')).order_by('pluginscript_data')
            catalog_url_prefix = 'catalog_urls?URL='
            for url in catalog_urls:
                url['item_link'] = catalog_url_prefix + urllib.quote(url['pluginscript_data'])

        except:
            catalog_urls = None

        # Machines using the default repo url
        http_munki = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='http://munki').count()

        # Machines using client certs
        client_certs = machines.filter(pluginscriptsubmission__plugin='MunkiInfo',pluginscriptsubmission__pluginscriptrow__pluginscript_name='UseClientCertificate', pluginscriptsubmission__pluginscriptrow__pluginscript_data='True').count()

        c = Context({
            'title': 'Munki Info',
            'http_only': http_only,
            'https_only': https_only,
            'http_munki': http_munki,
            'repo_urls': repo_urls,
            'catalog_urls': catalog_urls,
            'manifest_urls': manifest_urls,
            'package_urls': package_urls,
            'client_certs': client_certs,
            'plugin': 'MunkiInfo',
            'page': page,
            'theid': theid
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.
        print data
        if data.startswith('http_only?'):
            try:
                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='http://')
            except:
                machines = None
            title = 'Machines using HTTP'

        if data.startswith('https_only?'):
            try:
                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__startswith='https://')
            except:
                machines = None
            title = 'Machines using HTTPS'

        if data.startswith('http_munki?'):
            try:
                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='http://munki')
            except:
                machines = None
            title = 'Machines connecting to Munki using http://munki'

        if data.startswith('client_certs?'):
            try:
                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo',pluginscriptsubmission__pluginscriptrow__pluginscript_name='UseClientCertificate', pluginscriptsubmission__pluginscriptrow__pluginscript_data='True')
            except:
                machines = None
            title = 'Machines connecting to Munki using client certificates'

        if data.startswith('repo_urls?'):

            url_re = re.search('repo_urls\?URL=\"(.*)\"', data)
            url = urllib.unquote(url_re.group(1))

            try:

                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='SoftwareRepoURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact=url)
            except:
                machines = None
            title = 'Machines using %s' % url

        if data.startswith('manifest_urls?'):

            url_re = re.search('manifest_urls\?URL=\"(.*)\"', data)
            url = urllib.unquote(url_re.group(1))

            try:

                machines = machines.filter(pluginscriptsubmission__plugin='MunkiInfo', pluginscriptsubmission__pluginscriptrow__pluginscript_name='ManifestURL', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact=url)
            except:
                machines = None
            title = 'Machines using %s' % url

        return machines, title
