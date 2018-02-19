import requests
from datetime import datetime

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import loader, Context
from django.utils.dateparse import parse_datetime

from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager

import server.utils as utils


class CryptStatus(IPlugin):
    def plugin_type(self):
        return 'machine_detail'

    def supported_os_families(self):
        return ['Darwin']

    def widget_width(self):
        return 4

    def get_description(self):
        return 'FileVault Escrow Status'

    def widget_content(self, page, machines=None, theid=None):

        t = loader.get_template('cryptstatus/templates/cryptstatus.html')

        crypt_url = utils.get_setting('crypt_url', '').rstrip()
        machine_url = crypt_url

        try:
            cert = settings.ROOT_CA
        except Exception:
            cert = None

        serial = machines.serial
        output = {}
        date_escrowed = None
        escrowed = None
        if crypt_url:
            request_url = crypt_url + '/verify/' + serial + '/recovery_key/'
            if cert is not None:
                verify = cert
            else:
                verify = True
            try:
                response = requests.get(request_url, verify=verify)
                if response.status_code == requests.codes.ok:
                    output = response.json()
                    machine_url = '{}/info/{}'.format(crypt_url, serial)
            except Exception:
                pass

        if output != {}:
            escrowed = output['escrowed']
            if output['escrowed']:
                date_escrowed = parse_datetime(output['date_escrowed'])

        c = Context({
            'title': 'FileVault Escrow',
            'date_escrowed': date_escrowed,
            'escrowed': escrowed,
            'crypt_url': machine_url
        })
        return t.render(c)

    def filter_machines(self, machines, data):

        machines = machines.filter(operating_system__exact=data)

        return machines, 'Machines running ' + data
