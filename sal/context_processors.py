from django.conf import settings # import the settings file

def display_name(request):
    # return the value you want as a dictionary. you may add multiple values in there.
    return {'DISPLAY_NAME': settings.DISPLAY_NAME}

def config_installed(request):
    if 'config' in settings.INSTALLED_APPS:
        return {'CONFIG_INSTALLED': True}

    else:
        return {'CONFIG_INSTALLED': False}