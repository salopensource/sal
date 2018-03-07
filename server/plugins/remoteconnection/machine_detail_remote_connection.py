"""Machine detail plugin to allow easy VNC or SSH connections."""


import sal.plugin
from server.models import Machine, SalSetting
from server.utils import get_setting


class RemoteConnection(sal.plugin.DetailPlugin):

    description = "Initiate VNC or SSH connections from a machine detail page."

    def get_context(self, queryset, **kwargs):
        context = self.super_context(queryset, **kwargs)

        ip_address = ""
        if queryset.conditions.count() > 0:
            try:
                ip_addresses = queryset.conditions.get(
                    condition_name="ipv4_address").condition_data
                # Machines may have multiple IPs. Just use the first.
                ip_address = ip_addresses.split(",")[0]
            except Machine.DoesNotExist:
                pass

        context['ssh_account'] = get_setting(name='ssh_account', default='').replace('@', '')
        context["ssh_url"] = "ssh://{}{}".format(context['ssh_account'], ip_address)
        context["vnc_url"] = "vnc://{}{}".format(context['ssh_account'], ip_address)

        return context
