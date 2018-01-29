#!/usr/bin/python
"""Machine detail plugin to allow easy VNC or SSH connections."""


from django.conf import settings
from django.template import loader
from yapsy.IPlugin import IPlugin

from server.models import Machine


class RemoteConnection(IPlugin):

    def plugin_type(self):
        return "machine_detail"

    def widget_width(self):
        return 4

    def get_description(self):
        return "Initiate VNC or SSH connections from a machine detail page."

    def widget_content(self, page, machines=None, theid=None):
        # Rename class keyword argument to be more accurate, since it will
        # only be a single machine.
        machine = machines
        template = loader.get_template(
            "machine_detail_remote_connection/templates/"
            "machine_detail_remote_connection.html")

        ip_address = ""
        if machine.conditions.count() > 0:
            try:
                ip_addresses = machine.conditions.get(
                    condition_name="ipv4_address").condition_data
                # Machines may have multiple IPs. Just use the first.
                ip_address = ip_addresses.split(",")[0]
            except Machine.DoesNotExist:
                pass

        if hasattr(settings, "SSH_ACCOUNT") and settings.SSH_ACCOUNT:
            ssh_account = settings.SSH_ACCOUNT + "@"
        else:
            ssh_account = ""

        context = {
            "title": "Remote Connection",
            "ssh_account": ssh_account.replace("@", ""),
            "vnc_url": "vnc://{}{}".format(ssh_account, ip_address),
            "ssh_url": "ssh://{}{}".format(ssh_account, ip_address),}

        return template.render(context)
