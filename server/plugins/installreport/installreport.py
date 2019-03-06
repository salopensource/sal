import json
import plistlib
import re
import urllib.parse

from django.shortcuts import get_object_or_404

import sal.plugin
from catalog.models import Catalog
from server.models import BusinessUnit, ManagedItem, ManagementSource


class InstallReport(sal.plugin.ReportPlugin):

    description = 'Information on installation status.'
    supported_os_families = [sal.plugin.OSFamilies.darwin]

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
            safe_data = plistlib.loads(catalog.content.encode())
            for pkginfo in safe_data:
                description_dict[pkginfo['name'], pkginfo['version']] = pkginfo.get(
                    'description', '')

        output = []
        try:
            munki = ManagementSource.objects.get(name='Munki')
        except ManagementSource.DoesNotExist:
            munki = None

        installed_updates = (
            ManagedItem.objects
            .filter(machine__in=machines, management_source=munki)
            .values('name')
            .order_by()
            .distinct())

        for installed_update in installed_updates:
            item = {'name': installed_update['name']}

            update_queryset = (
                ManagedItem.objects
                .filter(
                    machine__in=machines,
                    name=installed_update['name'],
                    management_source=munki))

            item['install_count'] = update_queryset.filter(status='PRESENT').count()
            item['pending_count'] = update_queryset.filter(status='PENDING').count()

            first = update_queryset.first()
            item = self._get_metadata(item, first)
            item = self._css_clean(item)
            link_name = urllib.parse.urlencode({'NAME': item['name']})
            item['installed_url'] = f'PRESENT?{link_name}'
            item['pending_url'] = f'PENDING?{link_name}'

            output.append(item)

        context['output'] = sorted(output, key=lambda k: k['name'])
        context['title'] = 'Install Report'
        return context

    def filter(self, machines, data):
        try:
            url_tuple = urllib.parse.urlparse(data)
        except ValueError:
            return None, None

        status = url_tuple.path
        if not status:
            return None, None

        queries = urllib.parse.parse_qs(url_tuple.query)
        try:
            name = queries.get('NAME', [''])[0]
        except IndexError:
            return None, None

        if not name:
            return None, None

        try:
            munki = ManagementSource.objects.get(name='Munki')
        except ManagementSource.DoesNotExist:
            return None, None

        title = f'Machines with {name} {status}'

        machines = machines.filter(
            manageditem__name=name,
            manageditem__status=status,
            manageditem__management_source=munki)

        return machines, title

    def _css_clean(self, item):
        item['css_name'] = item['name'].replace('.', 'DOT')
        item['css_name'] = re.sub(r'\W+', '', item['css_name'])
        return item

    def _get_metadata(self, report_item, managed_item):
        try:
            data = json.loads(managed_item.data)
        except Exception:
            data = {}

        report_item['description'] = data.get('description', '')
        report_item['version'] = data.get('installed_version') or data.get('version_to_install', '')

        return report_item
