import plistlib

from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from catalog.models import Catalog
from sal.decorators import key_auth_required
from server.models import MachineGroup
from utils import text_utils


@csrf_exempt
@require_POST
@key_auth_required
def submit_catalog(request):
    submission = request.POST
    key = submission.get('key')
    name = submission.get('name')
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404

        compressed_catalog = submission.get('base64bz2catalog')
        if compressed_catalog:
            catalog_bytes = text_utils.decode_submission_data(compressed_catalog, 'base64bz2')
            if text_utils.is_valid_plist(catalog_bytes):
                try:
                    catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                except Catalog.DoesNotExist:
                    catalog = Catalog(name=name, machine_group=machine_group)
                catalog.sha256hash = submission.get('sha256hash')
                # Convert bytes to str for storage
                catalog.content = catalog_bytes.decode()
                catalog.save()
    return HttpResponse("Catalogs submitted.")


@csrf_exempt
@require_POST
@key_auth_required
def catalog_hash(request):
    submission = request.POST
    key = submission.get('key')
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404

    output = []
    catalogs = submission.get('catalogs')
    if catalogs:
        catalogs_plist = text_utils.submission_plist_loads(catalogs, 'base64bz2')
        if catalogs_plist:
            for item in catalogs_plist:
                name = item['name']
                try:
                    found_catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                    output.append({'name': name, 'sha256hash': found_catalog.sha256hash})
                except Catalog.DoesNotExist:
                    output.append({'name': name, 'sha256hash': 'NOT FOUND'})

    return HttpResponse(plistlib.dumps(output))
