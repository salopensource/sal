from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from catalog.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
import plistlib
import re


class InstallReport(IPlugin):
    def plugin_type(self):
        return 'report'

    def widget_width(self):
        return 12

    def get_description(self):
        return 'Information on installation status.'

    def get_title(self):
        return 'Install Report'

    def safe_unicode(self, s):
        if isinstance(s, unicode):
            return s.encode('utf-8', errors='replace')
        else:
            return s

    def replace_dots(self, item):
        # item['name'] = item['pkginfo']['name']
        item['dotVersion'] = item['version'].replace('.', 'DOT')
        item['dotVersion'] = re.sub(r'\W+', '', item['dotVersion'])
        item['dotName'] = item['name'].replace('.', 'DOT')
        item['dotName'] = re.sub(r'\W+', '', item['dotName'])
        return item

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('installreport/templates/front.html')
            catalog_objects = Catalog.objects.all()

        if page == 'bu_dashboard':
            t = loader.get_template('installreport/templates/id.html')
            business_unit = get_object_or_404(BusinessUnit, pk=theid)
            machine_groups = business_unit.machinegroup_set.all()
            catalog_objects = Catalog.objects.filter(machine_group=machine_groups)

        if page == 'group_dashboard':
            t = loader.get_template('installreport/templates/id.html')
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            catalog_objects = Catalog.objects.filter(machine_group=machine_group)

        output = []
        # Get the install reports for the machines we're looking for
        installed_updates = InstalledUpdate.objects.filter(machine__in=machines).values(
            'update', 'display_name', 'update_version').order_by().distinct()
        for catalog in catalog_objects:
            catalog.content = plistlib.readPlistFromString(self.safe_unicode(catalog.content))
        for installed_update in installed_updates:
            found = False
            for item in output:
                #print item
                if installed_update['update'] == item['name'] and installed_update['update_version'] == item['version']:
                    found = True
                    break

            if found == False:
                item = {}
                for catalog in catalog_objects:

                    for pkginfo in catalog.content:
                        if pkginfo['name'] == installed_update['update'] and pkginfo['version'] == installed_update['update_version']:
                            #print pkginfo
                            if 'description' in pkginfo:
                                item['description'] = pkginfo['description']
                            else:
                                item['description'] = ''
                            break
                    if 'description' in item:
                        break

                item['version'] = installed_update['update_version']
                item['name'] = installed_update['update']
                item['install_count'] = InstalledUpdate.objects.filter(
                    machine__in=machines, update=installed_update['update'], update_version=installed_update['update_version'], installed=True).count()

                item['pending_count'] = PendingUpdate.objects.filter(
                    machine__in=machines, update=installed_update['update'], update_version=installed_update['update_version']).count()
                item['installed_url'] = 'Installed?VERSION=%s&&NAME=%s' % (
                    item['version'], item['name'])
                item['pending_url'] = 'Pending?VERSION=%s&&NAME=%s' % (
                    item['version'], item['name'])
                item = self.replace_dots(item)

                output.append(item)

        # Sort the output
        output = sorted(output, key=lambda k: (k['name'], k['version']))
        c = Context({
            'title': 'Install Reports',
            'output': output,
            'plugin': 'InstallReport',
            'page': page,
            'theid': theid
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        if data.startswith('Installed?'):
            version_re = re.search('Installed\?VERSION\=(.*)&&NAME', data)
            version = version_re.group(1)
            name_re = re.search('&&NAME=(.*)', data)
            name = name_re.group(1)

            machines = machines.filter(
                installed_updates__update=name, installed_updates__update_version=version, installed_updates__installed=True)
            title = 'Machines with %s %s installed' % (name, version)

        if data.startswith('Pending?'):
            version_re = re.search('Pending\?VERSION\=(.*)&&NAME', data)
            version = version_re.group(1)
            name_re = re.search('&&NAME=(.*)', data)
            name = name_re.group(1)

            machines = machines.filter(pending_updates__update=name,
                                       pending_updates__update_version=version)
            title = 'Machines with %s %s pending' % (name, version)

        return machines, title
