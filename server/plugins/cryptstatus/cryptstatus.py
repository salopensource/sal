from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.conf import settings
import requests
from datetime import datetime
from django.utils.dateparse import parse_datetime


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

        try:
            crypt_url = settings.CRYPT_URL
            crypt_url = crypt_url.rstrip('/')
        except Exception:
            crypt_url = None

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
            if cert != None:
                verify = cert
            else:
                verify = True
            try:
                r = requests.get(request_url, verify=verify)
                if r.status_code == requests.codes.ok:
                    output = r.json()
            except Exception:
                pass

        if output != {}:
            escrowed = output['escrowed']
            if output['escrowed'] == True:
                date_escrowed = parse_datetime(output['date_escrowed'])

        c = Context({
            'title': 'FileVault Escrow',
            'date_escrowed': date_escrowed,
            'escrowed': escrowed,
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        machines = machines.filter(operating_system__exact=data)

        return machines, 'Machines running ' + data
