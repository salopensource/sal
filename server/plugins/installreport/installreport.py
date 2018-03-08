import plistlib
import re

from django.shortcuts import get_object_or_404

from catalog.models import Catalog
from server.models import BusinessUnit, InstalledUpdate, PendingUpdate
from server.utils import safe_unicode
import sal.plugin


class InstallReport(sal.plugin.ReportPlugin):

    description = 'Information on installation status.'

    def replace_dots(self, item):
        # item['name'] = item['pkginfo']['name']
        item['dotVersion'] = item['version'].replace('.', 'DOT')
        item['dotVersion'] = re.sub(r'\W+', '', item['dotVersion'])
        item['dotName'] = item['name'].replace('.', 'DOT')
        item['dotName'] = re.sub(r'\W+', '', item['dotName'])
        return item

    def get_context(self, machines, group_type='all', group_id=None):
        context = self.super_get_context(machines, group_type=group_type, group_id=group_id)
        catalog_objects = Catalog.objects.all()
        if group_type == 'business_unit':
            business_unit = get_object_or_404(BusinessUnit, pk=group_id)
            catalog_objects = catalog_objects.filter(machine_group__business_unit=business_unit)
        elif group_type == 'machine_group':
            catalog_objects = catalog_objects.filter(machine_group__pk=group_id)

        description_dict = {}
        for catalog in catalog_objects:
            safe_data = plistlib.readPlistFromString(safe_unicode(catalog.content))
            for pkginfo in safe_data:
                description_dict[pkginfo['name'], pkginfo['version']] = pkginfo.get(
                    'description', '')

        output = []
        # Get the install reports for the machines we're looking for
        installed_updates = InstalledUpdate.objects.filter(machine__in=machines).values(
            'update', 'display_name', 'update_version').order_by().distinct()

        for installed_update in installed_updates:
            item = {}
            item['version'] = installed_update['update_version']
            item['name'] = installed_update['update']
            item['description'] = description_dict.get((item['name'], item['version']), '')
            item['install_count'] = InstalledUpdate.objects.filter(
                machine__in=machines,
                update=installed_update['update'],
                update_version=installed_update['update_version'],
                installed=True).count()

            item['pending_count'] = PendingUpdate.objects.filter(
                machine__in=machines,
                update=installed_update['update'],
                update_version=installed_update['update_version']).count()

            item['installed_url'] = 'Installed?VERSION=%s&&NAME=%s' % (
                item['version'], item['name'])
            item['pending_url'] = 'Pending?VERSION=%s&&NAME=%s' % (
                item['version'], item['name'])

            item = self.replace_dots(item)

            output.append(item)

        context['output'] = sorted(output, key=lambda k: (k['name'], k['version']))
        return context

    def filter(self, machines, data):
        if data.startswith('Installed?'):
            version_re = re.search('Installed\?VERSION\=(.*)&&NAME', data)
            version = version_re.group(1)
            name_re = re.search('&&NAME=(.*)', data)
            name = name_re.group(1)

            machines = machines.filter(
                installed_updates__update=name,
                installed_updates__update_version=version,
                installed_updates__installed=True)
            title = 'Machines with %s %s installed' % (name, version)

        elif data.startswith('Pending?'):
            version_re = re.search('Pending\?VERSION\=(.*)&&NAME', data)
            version = version_re.group(1)
            name_re = re.search('&&NAME=(.*)', data)
            name = name_re.group(1)

            machines = machines.filter(pending_updates__update=name,
                                       pending_updates__update_version=version)
            title = 'Machines with %s %s pending' % (name, version)

        else:
            return None, None

        return machines, title
