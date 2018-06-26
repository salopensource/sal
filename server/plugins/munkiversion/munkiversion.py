from django.db.models import Count

import sal.plugin


class MunkiVersion(sal.plugin.Widget):

    description = 'Chart of installed versions of Munki'
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        munki_info = queryset.values('munki_version').annotate(
            count=Count('munki_version')).order_by('munki_version')
        context['data'] = munki_info
        return context

    def filter(self, machines, data):
        machines = machines.filter(munki_version=data)
        title = 'Machines running version {} of MSC'.format(data)
        return machines, title
