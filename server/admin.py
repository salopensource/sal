from django.contrib import admin
from django.forms import ModelForm, ModelMultipleChoiceField

from server.models import *
from server.utils import reload_plugins_model


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


class MachineGroupInline(admin.TabularInline):
    model = MachineGroup


class PluginScriptRowInline(admin.StackedInline):
    model = PluginScriptRow
    extra = 0


class UpdateHistoryItemInline(admin.TabularInline):
    model = UpdateHistoryItem
    extra = 0


class UserProfileInline(admin.StackedInline):
    model = UserProfile


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
    if isinstance(obj, MachineGroup):
        return Machine.objects.filter(machine_group=obj).count()
    else:
        return Machine.objects.filter(machine_group__in=obj.machinegroup_set.all()).count()


def business_unit(obj):
    return obj.machine_group.business_unit.name


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_key', 'private_key')


class BusinessUnitAdmin(admin.ModelAdmin):
    inlines = [MachineGroupInline, ]
    form = BusinessUnitForm
    list_display = ('name', number_of_users, number_of_machine_groups, number_of_machines)
    fields = (('name', number_of_users, number_of_machine_groups, number_of_machines), 'users')
    readonly_fields = (number_of_users, number_of_machine_groups, number_of_machines)


class ConditionAdmin(admin.ModelAdmin):
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'condition_name')
    list_display = ('condition_name', 'condition_data', 'machine')
    search_fields = ('condition_name', 'condition_data', 'machine__hostname')


class FactAdmin(admin.ModelAdmin):
    list_display = ('fact_name', 'fact_data', 'machine')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'fact_name')
    search_fields = ('fact_name', 'fact_data', 'machine__hostname')


class HistoricalFactAdmin(admin.ModelAdmin):
    list_display = ('fact_name', 'fact_data', 'machine', 'fact_recorded')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'fact_name')
    search_fields = ('fact_name', 'fact_data', 'machine__hostname')
    date_hierarchy = 'fact_recorded'


class InstalledUpdateAdmin(admin.ModelAdmin):
    list_display = ('update', 'display_name', 'machine', 'update_version', 'installed')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'update')
    search_fields = ('machine__hostname', 'display_name', 'update')


class MachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'serial', 'machine_model', 'operating_system', 'deployed')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'operating_system', 'os_family',
                   'machine_model', 'last_checkin', 'errors', 'warnings', 'puppet_errors',
                   'deployed')
    fields = (
        (business_unit, 'machine_group'),
        ('hostname', 'serial', 'console_user'),
        ('machine_model', 'machine_model_friendly'),
        ('cpu_type', 'cpu_speed'), ('memory', 'memory_kb'), ('hd_space', 'hd_total', 'hd_percent'),
        ('operating_system', 'os_family'),
        ('munki_version', 'manifest', 'errors', 'warnings'),
        ('last_checkin', 'first_checkin'),
        ('puppet_version', 'last_puppet_run', 'puppet_errors'),
        ('sal_version', 'deployed', 'broken_client'),
        'report', 'report_format', 'install_log_hash', 'install_log'
    )
    readonly_fields = (business_unit, 'first_checkin', 'last_checkin', 'last_puppet_run',
                       'report_format')
    search_fields = ('hostname', 'console_user')


class MachineDetailPluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'os_families')
    list_filter = ('os_families',)

    def get_queryset(self, request):
        """Update db prior to retrieving plugins.

        Views listing MachineDetailPlugins must first update the list of
        installed plugins and update their descriptions and types.
        """
        reload_plugins_model()
        return super(MachineDetailPluginAdmin, self).get_queryset(request)


class MachineGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_unit', number_of_machines)
    list_filter = (BusinessUnitFilter,)
    fields = ('name', 'business_unit', number_of_machines, 'key')
    readonly_fields = (number_of_machines, 'key')


class PendingUpdateAdmin(admin.ModelAdmin):
    list_filter = (BusinessUnitFilter, MachineGroupFilter)
    list_display = ('update', 'display_name', 'update_version', 'machine')
    search_fields = ('update', 'display_name', 'machine__hostname')


class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'type')
    list_filter = ('type',)

    def get_queryset(self, request):
        """Update db prior to retrieving plugins.

        Views listing Plugins must first update the list of
        installed plugins and update their descriptions and types.
        """
        reload_plugins_model()
        return super(PluginAdmin, self).get_queryset(request)


class PluginScriptRowAdmin(admin.ModelAdmin):
    search_fields = ('plugin',)


class PluginScriptSubmissionAdmin(admin.ModelAdmin):
    inlines = [PluginScriptRowInline, ]
    list_display = ('plugin', 'machine', 'recorded', 'historical')
    list_filter = (BusinessUnitFilter, MachineGroupFilter, 'plugin', 'historical', 'recorded')
    search_fields = ('plugin', 'machine__hostname')
    date_hierarchy = 'recorded'


class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

    def get_queryset(self, request):
        """Update db prior to retrieving plugins.

        Views listing MachineDetailPlugins must first update the list of
        installed plugins and update their descriptions and types.
        """
        reload_plugins_model()
        return super(ReportAdmin, self).get_queryset(request)


class SalSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')


class UpdateHistoryAdmin(admin.ModelAdmin):
    inlines = [UpdateHistoryItemInline, ]
    list_display = ('name', 'machine', 'update_type', 'version')
    list_filter = ('update_type', BusinessUnitFilter, MachineGroupFilter)
    search_fields = ('name', 'machine__hostname', 'version')


class UpdateHistoryItemAdmin(admin.ModelAdmin):
    search_fields = ('update_history__name', 'update_history__machine__hostname')
    list_display = ('update_history', 'recorded', 'status')
    date_hierarchy = 'recorded'


class CustomUserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'profile_level', 'last_login')
    list_filter = ('userprofile__level',)
    search_fields = ('username', )
    fields = (
        ('username', 'first_name', 'last_name', 'email'),
        ('is_staff', 'is_active'),
        ('last_login', 'date_joined'),
    )

    def profile_level(self, user):
        return user.userprofile.level


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(BusinessUnit, BusinessUnitAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(Fact, FactAdmin)
admin.site.register(HistoricalFact, HistoricalFactAdmin)
admin.site.register(InstalledUpdate, InstalledUpdateAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MachineDetailPlugin, MachineDetailPluginAdmin)
admin.site.register(MachineGroup, MachineGroupAdmin)
admin.site.register(PendingAppleUpdate, PendingUpdateAdmin)
admin.site.register(PendingUpdate, PendingUpdateAdmin)
admin.site.register(Plugin, PluginAdmin)
admin.site.register(PluginScriptRow, PluginScriptRowAdmin)
admin.site.register(PluginScriptSubmission, PluginScriptSubmissionAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(SalSetting, SalSettingAdmin)
admin.site.register(UpdateHistory, UpdateHistoryAdmin)
admin.site.register(UpdateHistoryItem, UpdateHistoryItemAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
