from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions

from server.models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """Use publickey/privatekey HTTP headers for authentication"""

    def authenticate(self, request):
        public_key = request.META.get('HTTP_PUBLICKEY', False)
        private_key = request.META.get('HTTP_PRIVATEKEY', False)
        if not any((public_key, private_key)):
            return None

        try:
            api_key = ApiKey.objects.get(
                private_key=private_key, public_key=public_key)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')

        return (api_key, None)


class HasRWPermission(permissions.BasePermission):
    """Only allow Users with staff status or RW API keys."""

    def has_permission(self, request, view):
        # Grant Sal Users access based on 'staff' membership; i.e.
        # 'Global Admin'.
        if isinstance(request.user, User):
            return request.user.is_staff
        # Otherwise, all API token that has passed auth can perform
        # 'safe' methods.
        elif isinstance(request.user, ApiKey):
            if request.method in permissions.SAFE_METHODS:
                return True
            # Write permissions are only allowed to keys that have RW.
            return request.user.read_write
        else:
            # If authentication fails, the user will be of type
            # django.contrib.auth.models.AnonymousUser;
            # reject anonymous users.
            return False
