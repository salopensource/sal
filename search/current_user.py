from threading import local

from django.utils.deprecation import MiddlewareMixin


_user = local()


class CurrentUserMiddleware(MiddlewareMixin):

    def process_request(self, request):
        _user.value = request.user


def get_current_user():
    try:
        return _user.value
    except Exception:
        return None
