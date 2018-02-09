from django.contrib import admin
from django.forms import ModelForm, ModelMultipleChoiceField

from server.models import *


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_key', 'private_key')


class MachineGroupInline(admin.TabularInline):
    model = MachineGroup


class BusinessUnitForm(ModelForm):

    class Meta:
        model = BusinessUnit
        fields = ['name', 'users']

    users = ModelMultipleChoiceField(
        queryset=User.objects.exclude(userprofile__level='GA'),
        label=('Members'),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple(verbose_name="Users", is_stacked=False))


def number_of_users(obj):
    return obj.users.count()


def number_of_machine_groups(obj):
    return obj.machinegroup_set.count()


def number_of_machines(obj):
    return Machine.objects.filter(machine_group__in=obj.machinegroup_set.all()).count()


class BusinessUnitAdmin(admin.ModelAdmin):
    inlines = [MachineGroupInline,]
    form = BusinessUnitForm
    list_display = ('name', number_of_users, number_of_machine_groups, number_of_machines)
    fields = (('name', number_of_users, number_of_machine_groups, number_of_machines), 'users')
    readonly_fields = (number_of_users, number_of_machine_groups, number_of_machines)


class BusinessUnitFilter(admin.SimpleListFilter):
    title = 'Business Unit'
    parameter_name = 'business_unit'

    def lookups(self, request, model_admin):
        return ((bu.name, bu.name) for bu in BusinessUnit.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(machine__machine_group__business_unit__name=self.value())
        else:
            return queryset


class MachineGroupFilter(admin.SimpleListFilter):
    title = 'Machine Group'
    parameter_name = 'machine_group'

    def lookups(self, request, model_admin):
        return ((mg.name, mg.name) for mg in MachineGroup.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(machine__machine_group__name=self.value())
        else:
            return queryset


class ConditionAdmin(admin.ModelAdmin):
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'condition_name')


class FactAdmin(admin.ModelAdmin):
    list_display = ('fact_name', 'fact_data')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'fact_name')


class HistoricalFactAdmin(admin.ModelAdmin):
    list_display = ('fact_name', 'fact_data', 'fact_recorded')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'fact_name')


class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'serial')


class MachineGroupAdmin(admin.ModelAdmin):
    readonly_fields = ('key',)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(BusinessUnit, BusinessUnitAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(Fact, FactAdmin)
admin.site.register(HistoricalFact, HistoricalFactAdmin)
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
