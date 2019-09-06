"""Machine detail plugin to allow easy VNC or SSH connections."""


import sal.plugin
from server.models import Fact
from server.utils import get_setting


class RemoteConnection(sal.plugin.DetailPlugin):

    description = "Initiate VNC or SSH connections from a machine detail page."
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        ip_address = ""
        if queryset.facts.count() > 0:
            try:
                ip_addresses = queryset.facts.get(
                    fact_name="ipv4_address").fact_data
                # Machines may have multiple IPs. Just use the first.
                ip_address = ip_addresses.split(",")[0]
            except Fact.DoesNotExist:
                pass

        account = get_setting(name='ssh_account', default='').strip()
        context['ssh_account'] = account
        delimiter = '' if not account else '@'
        context["ssh_url"] = "ssh://{}{}{}".format(account, delimiter, ip_address)
        context["vnc_url"] = "vnc://{}{}{}".format(account, delimiter, ip_address)

        return context
