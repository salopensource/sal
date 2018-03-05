import requests
from collections import defaultdict
from requests.exceptions import RequestException

from django.conf import settings
from django.utils.dateparse import parse_datetime

import server.utils as utils
from sal.plugin import DetailPlugin


class CryptStatus(DetailPlugin):

    class Meta:
        description = 'FileVault Escrow Status'

    def get_context(self, machine, **kwargs):
        context = defaultdict(str)
        context['title'] = self.Meta.description

        crypt_url = utils.get_setting('crypt_url', '').rstrip()
        if crypt_url:
            try:
                verify = settings.ROOT_CA
            except AttributeError:
                verify = True

            request_url = '{}/verify/{}/recovery_key/'.format(crypt_url, machine.serial)
            try:
                response = requests.get(request_url, verify=verify)
                if response.status_code == requests.codes.ok:
                    output = response.json()
                    # Have template link to machine info page rather
                    # than Crypt root.
                    machine_url = '{}/info/{}'.format(crypt_url, machine.serial)
            except RequestException:
                # Either there was an error or the machine hasn't been
                # seen.
                output = None
                machine_url = crypt_url

            if output:
                context['escrowed'] = output['escrowed']
                if output['escrowed']:
                    context['date_escrowed'] = parse_datetime(output['date_escrowed'])

        context['crypt_url'] = machine_url
        return context
