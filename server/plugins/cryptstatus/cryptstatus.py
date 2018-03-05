import requests
from requests.exceptions import RequestException

from django.conf import settings
from django.utils.dateparse import parse_datetime

import server.utils as utils
from sal.plugin import DetailPlugin


class CryptStatus(DetailPlugin):

    class Meta:
        description = 'FileVault Escrow Status'

    def process(self, machine, **kwargs):
        crypt_url = utils.get_setting('crypt_url', '').rstrip()
        machine_url = crypt_url
        date_escrowed = None
        escrowed = None

        try:
            verify = settings.ROOT_CA
        except AttributeError:
            verify = True

        output = None
        if crypt_url:
            request_url = crypt_url + '/verify/' + machine.serial + '/recovery_key/'
            try:
                response = requests.get(request_url, verify=verify)
                if response.status_code == requests.codes.ok:
                    output = response.json()
                    # Have template link to machine info page rather
                    # than Crypt root.
                    machine_url = '{}/info/{}'.format(crypt_url, machine.serial)
            except RequestException:
                pass

            if output:
                escrowed = output['escrowed']
                if output['escrowed']:
                    date_escrowed = parse_datetime(output['date_escrowed'])

        context = {
            'title': 'FileVault Escrow',
            'date_escrowed': date_escrowed,
            'escrowed': escrowed,
            'crypt_url': machine_url}
        return context
