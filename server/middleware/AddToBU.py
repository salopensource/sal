from django.conf import settings
from server.models import *


class AddToBU(object):
    """
    This middleware will add the current user to any BU's they've not already
    been explicitly added to.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(settings, 'ADD_TO_ALL_BUSINESS_UNITS'):
            if request.user.is_authenticated():
                if settings.ADD_TO_ALL_BUSINESS_UNITS \
                        and request.user.userprofile.level != 'GA':
                    for business_unit in BusinessUnit.objects.all():
                        if request.user not in business_unit.users.all():
                            business_unit.users.add(request.user)
                            business_unit.save()

        return None
