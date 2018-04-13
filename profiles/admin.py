from django.contrib import admin
from profiles.models import *


class PayloadInline(admin.TabularInline):
    model = Payload


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'machine', 'uuid', 'install_date', 'verification_state')
    list_filter = ('identifier', 'machine', 'install_date', 'verification_state')
    search_fields = ('identifier', 'machine__hostname', 'payload__identifier')
    inlines = [
        PayloadInline,
    ]

admin.site.register(Profile, ProfileAdmin)
