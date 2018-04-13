from django.contrib import admin
from profiles.models import *

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'machine', 'uuid', 'install_date', 'verification_state')
    list_filter = ('identifier', 'machine', 'install_date', 'verification_state')


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'profile', 'uuid')
    list_filter = ('identifier', 'profile')
    search_fields = ('identifier',)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Payload, PayloadAdmin)
