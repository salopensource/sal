from django.contrib import admin
from server.models import *

class MachineGroupAdmin(admin.ModelAdmin):
    readonly_fields=('key',)

class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'serial')
admin.site.register(UserProfile)
admin.site.register(BusinessUnit)
admin.site.register(MachineGroup, MachineGroupAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Fact)
admin.site.register(PluginScriptSubmission)
admin.site.register(PluginScriptRow)
admin.site.register(HistoricalFact)
admin.site.register(Condition)
admin.site.register(PendingUpdate)
admin.site.register(InstalledUpdate)
admin.site.register(PendingAppleUpdate)
admin.site.register(ApiKey)
admin.site.register(Plugin)
admin.site.register(Report)
# admin.site.register(OSQueryResult)
# admin.site.register(OSQueryColumn)
admin.site.register(SalSetting)
admin.site.register(UpdateHistory)
admin.site.register(UpdateHistoryItem)
admin.site.register(MachineDetailPlugin)
