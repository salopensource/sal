from django.conf import settings # import the settings file

def display_name(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'DISPLAY_NAME': settings.DISPLAY_NAME}