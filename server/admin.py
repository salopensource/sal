from django.contrib import admin

from server.models import *


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_key', 'private_key')


class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'serial')


class MachineGroupAdmin(admin.ModelAdmin):
    readonly_fields = ('key',)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(BusinessUnit)
admin.site.register(Condition)
admin.site.register(Fact)
admin.site.register(HistoricalFact)
admin.site.register(InstalledUpdate)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MachineDetailPlugin)
admin.site.register(MachineGroup, MachineGroupAdmin)
# admin.site.register(OSQueryColumn)
# admin.site.register(OSQueryResult)
admin.site.register(PendingAppleUpdate)
admin.site.register(PendingUpdate)
admin.site.register(Plugin)
admin.site.register(PluginScriptRow)
admin.site.register(PluginScriptSubmission)
admin.site.register(Report)
admin.site.register(SalSetting)
admin.site.register(UpdateHistory)
admin.site.register(UpdateHistoryItem)
admin.site.register(UserProfile)
