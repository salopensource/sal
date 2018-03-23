from django.db.models import Count

import sal.plugin


class SalScriptsVersion(sal.plugin.Widget):

    description = 'Chart of installed versions of the Sal Scripts'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        context['sal_info'] = (
            queryset
            .values('sal_version')
            .exclude(sal_version__isnull=True)
            .annotate(count=Count('sal_version'))
            .order_by('sal_version'))

        return context

    def filter(self, machines, data):
        machines = machines.filter(sal_version__exact=data)
        title = 'Machines running version {} of Sal'.format(data)
        return machines, title
