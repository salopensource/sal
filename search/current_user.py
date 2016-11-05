from threading import local

_user = local()

class CurrentUserMiddleware(object):
    def process_request(self, request):
        _user.value = request.user

def get_current_user():
    try:
        return _user.value
    except:
        return None
