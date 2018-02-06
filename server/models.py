from django.db import models
from django.contrib.auth.models import User
import random
import string
import plistlib
from xml.parsers.expat import ExpatError
import base64
import bz2
from datetime import datetime
from watson import search as watson
from dateutil.parser import *

OS_CHOICES = (
    ('Darwin', 'macOS'),
    ('Windows', 'Windows'),
    ('Linux', 'Linux'),
)

REPORT_CHOICES = (
    ('base64', 'base64'),
    ('base64bz2', 'base64bz2'),
)


def GenerateKey():
    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(128))
    try:
        MachineGroup.objects.get(key=key)
        return GenerateKey()
    except MachineGroup.DoesNotExist:
        return key


def GenerateAPIKey():
    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(24))
    try:
        ApiKey.objects.get(public_key=key)
        return GenerateAPIKey()
    except ApiKey.DoesNotExist:
        return key


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)

    LEVEL_CHOICES = (
        ('SO', 'Stats Only'),
        ('RO', 'Read Only'),
        ('RW', 'Read Write'),
        ('GA', 'Global Admin'),
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='RO')

    def __unicode__(self):
        return self.user.username


User.userprofile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class BusinessUnit(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class MachineGroup(models.Model):
    business_unit = models.ForeignKey(BusinessUnit)
    name = models.CharField(max_length=100)
    key = models.CharField(db_index=True, max_length=255, unique=True,
                           blank=True, null=True, editable=False)

    def save(self, **kwargs):
        if not self.id:
            self.key = GenerateKey()
        super(MachineGroup, self).save()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class DeployedManager(models.Manager):
    def get_queryset(self):
        return super(DeployedManager, self).get_queryset().filter(deployed=True)


class Machine(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine_group = models.ForeignKey(MachineGroup)
    serial = models.CharField(db_index=True, max_length=100, unique=True)
    hostname = models.CharField(max_length=256, null=True, blank=True)
    operating_system = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    memory = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    memory_kb = models.IntegerField(db_index=True, default=0)
    munki_version = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    manifest = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    hd_space = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    hd_total = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    hd_percent = models.CharField(max_length=256, null=True, blank=True)
    console_user = models.CharField(max_length=256, null=True, blank=True)
    machine_model = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    machine_model_friendly = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    cpu_type = models.CharField(max_length=256, null=True, blank=True)
    cpu_speed = models.CharField(max_length=256, null=True, blank=True)
    os_family = models.CharField(db_index=True, max_length=256,
                                 choices=OS_CHOICES, verbose_name="OS Family", default="Darwin")
    last_checkin = models.DateTimeField(db_index=True, blank=True, null=True)
    first_checkin = models.DateTimeField(db_index=True, blank=True, null=True, auto_now_add=True)
    report = models.TextField(editable=True, null=True)
    report_format = models.CharField(
        max_length=256, choices=REPORT_CHOICES, default="base64bz2", editable=False)
    errors = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    activity = models.TextField(editable=False, null=True, blank=True)
    puppet_version = models.TextField(null=True, blank=True)
    sal_version = models.CharField(db_index=True, null=True, blank=True, max_length=255)
    last_puppet_run = models.DateTimeField(db_index=True, blank=True, null=True)
    puppet_errors = models.IntegerField(db_index=True, default=0)
    install_log_hash = models.CharField(max_length=200, blank=True, null=True)
    install_log = models.TextField(null=True, blank=True)
    deployed = models.BooleanField(default=True)
    broken_client = models.BooleanField(default=False)

    objects = models.Manager()  # The default manager.
    deployed_objects = DeployedManager()

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Machine._meta.fields]

    def encode(self, plist):
        string = plistlib.writePlistToString(plist)
        bz2data = bz2.compress(string)
        b64data = base64.b64encode(bz2data)
        return b64data

    def decode(self, data):
        # this has some sucky workarounds for odd handling
        # of UTF-8 data in sqlite3
        try:
            plist = plistlib.readPlistFromString(data)
            return plist
        except:
            try:
                plist = plistlib.readPlistFromString(data.encode('UTF-8'))
                return plist
            except:
                try:
                    if self.report_format == 'base64bz2':
                        return self.b64bz_decode(data)
                    elif self.report_format == 'base64':
                        return self.b64_decode(data)

                except:
                    return dict()

    def b64bz_decode(self, data):
        try:
            bz2data = base64.b64decode(data)
            string = bz2.decompress(bz2data)
            plist = plistlib.readPlistFromString(string)
            return plist
        except Exception:
            return {}

    def b64_decode(self, data):
        try:
            string = base64.b64decode(data)
            plist = plistlib.readPlistFromString(string)
            return plist
        except Exception:
            return {}

    def get_report(self):
        return self.decode(self.report)

    def get_activity(self):
        return self.decode(self.activity)

    def update_report(self, encoded_report, report_format='base64bz2'):
        # Save report.
        try:
            if report_format == 'base64bz2':
                base64bz2report = encoded_report.replace(" ", "+")
                plist = self.b64bz_decode(encoded_report)
            elif report_format == 'base64':
                base64report = encoded_report.replace(" ", "+")
                plist = self.b64_decode(encoded_report)
            self.report = plistlib.writePlistToString(plist)
            self.report_format = report_format
        except:
            plist = None
            self.report = ''

        if plist is None:
            self.activity = None
            self.errors = 0
            self.warnings = 0
            self.console_user = "<None>"
            return

        # Check activity.
        activity = dict()
        for section in ("ItemsToInstall",
                        "InstallResults",
                        "ItemsToRemove",
                        "RemovalResults",
                        "AppleUpdates"):
            if (section in plist) and len(plist[section]):
                activity[section] = plist[section]
        if activity:
            #self.activity = self.encode(activity)
            self.activity = plistlib.writePlistToString(activity)
        else:
            self.activity = None

        # Check errors and warnings.
        if "Errors" in plist:
            self.errors = len(plist["Errors"])
        else:
            self.errors = 0

        if "Warnings" in plist:
            self.warnings = len(plist["Warnings"])
        else:
            self.warnings = 0

        # Check console user.
        self.console_user = "unknown"
        if "ConsoleUser" in plist:
            self.console_user = unicode(plist["ConsoleUser"])

    def __unicode__(self):
        if self.hostname:
            return self.hostname
        else:
            return self.serial

    class Meta:
        ordering = ['hostname']

    def save(self, *args, **kwargs):
        self.serial = self.serial.replace('/', '')
        self.serial = self.serial.replace('+', '')
        if not self.hostname:
            self.hostname = self.serial
        super(Machine, self).save()


class UpdateHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    UPDATE_TYPE = (
        ('third_party', '3rd Party'),
        ('apple', 'Apple'),
    )
    machine = models.ForeignKey(Machine)
    update_type = models.CharField(max_length=254, choices=UPDATE_TYPE, verbose_name="Update Type")
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=254, db_index=True)
    pending_recorded = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s: %s %s" % (self.machine, self.name, self.version)

    class Meta:
        ordering = ['name']
        unique_together = (("machine", "name", "version", "update_type"),)


class UpdateHistoryItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    UPDATE_STATUS = (
        ('pending', 'Pending'),
        ('error', 'Error'),
        ('install', 'Install'),
        ('removal', 'Removal')
    )
    update_history = models.ForeignKey(UpdateHistory)
    recorded = models.DateTimeField()
    uuid = models.CharField(null=True, blank=True, max_length=100)
    status = models.CharField(max_length=254, choices=UPDATE_STATUS, verbose_name="Status")
    extra = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u"%s: %s %s %s %s" % (self.update_history.machine, self.update_history.name, self.update_history.version, self.status, self.recorded)

    class Meta:
        ordering = ['-recorded']
        unique_together = (("update_history", "recorded", "status"),)


class Fact(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='facts')
    fact_name = models.TextField(db_index=True)
    fact_data = models.TextField()

    def __unicode__(self):
        return u'%s: %s' % (self.fact_name, self.fact_data)

    class Meta:
        ordering = ['fact_name']


class HistoricalFact(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='historical_facts')
    fact_name = models.CharField(db_index=True, max_length=255)
    fact_data = models.TextField()
    fact_recorded = models.DateTimeField(db_index=True)

    def __unicode__(self):
        return self.fact_name

    class Meta:
        ordering = ['fact_name', 'fact_recorded']


class Condition(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='conditions')
    condition_name = models.CharField(max_length=255, db_index=True)
    condition_data = models.TextField(db_index=True)

    def __unicode__(self):
        return self.condition_name

    class Meta:
        ordering = ['condition_name']


class PluginScriptSubmission(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine)
    plugin = models.CharField(db_index=True, max_length=255)
    historical = models.BooleanField(default=False)
    recorded = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s: %s' % (self.machine, self.plugin)

    class Meta:
        ordering = ['recorded', 'plugin']


class PluginScriptRow(models.Model):
    id = models.BigAutoField(primary_key=True)
    submission = models.ForeignKey(PluginScriptSubmission)
    pluginscript_name = models.TextField(db_index=True)
    pluginscript_data = models.TextField(blank=True, null=True, db_index=True)
    pluginscript_data_string = models.TextField(blank=True, null=True, db_index=True)
    pluginscript_data_int = models.IntegerField(default=0)
    pluginscript_data_date = models.DateTimeField(blank=True, null=True)
    submission_and_script_name = models.TextField(db_index=True)

    def save(self):
        try:
            self.pluginscript_data_int = int(self.pluginscript_data)
        except:
            self.pluginscript_data_int = 0

        try:
            self.pluginscript_data_string = str(self.pluginscript_data)
        except:
            self.pluginscript_data_string = ""

        try:
            self.pluginscript_data_date = parse(self.pluginscript_data)
        except:
            # Try converting it to an int if we're here
            try:
                if int(self.pluginscript_data) != 0:

                    try:
                        self.pluginscript_data_date = datetime.fromtimestamp(
                            int(self.pluginscript_data))
                    except:
                        self.pluginscript_data_date = None
                else:
                    self.pluginscript_data_date = None
            except:
                self.pluginscript_data_date = None

        super(PluginScriptRow, self).save()

    def __unicode__(self):
        return u'%s: %s' % (self.pluginscript_name, self.pluginscript_data)

    class Meta:
        ordering = ['pluginscript_name']


class PendingUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='pending_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.update

    class Meta:
        ordering = ['display_name']


class InstalledUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='installed_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    installed = models.BooleanField()

    def __unicode__(self):
        return self.update

    class Meta:
        ordering = ['display_name']
        unique_together = ("machine", "update", "update_version")


class PendingAppleUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='pending_apple_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(db_index=True, max_length=256, null=True, blank=True)
    display_name = models.CharField(max_length=256, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.update) or u''

    class Meta:
        ordering = ['display_name']


class Plugin(models.Model):
    PLUGIN_TYPES = (
        ('facter', 'Facter'),
        ('munkicondition', 'Munki Condition'),
        ('builtin', 'Built In'),
        ('custom', 'Custom Script'),
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField()
    type = models.CharField(max_length=255, choices=PLUGIN_TYPES, default='builtin')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['order']


class MachineDetailPlugin(models.Model):
    PLUGIN_TYPES = (
        ('facter', 'Facter'),
        ('munkicondition', 'Munki Condition'),
        ('builtin', 'Built In'),
        ('custom', 'Custom Script'),
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField()
    os_families = models.CharField(db_index=True, max_length=256,
                                   verbose_name="OS Family", default="Darwin")
    type = models.CharField(max_length=255, choices=PLUGIN_TYPES, default='builtin')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['order']


class Report(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SalSetting(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __unicode__(self):
        return self.name


class ApiKey(models.Model):
    public_key = models.CharField(db_index=True, max_length=255)
    private_key = models.CharField(db_index=True, max_length=255)
    name = models.CharField(max_length=255)
    has_been_seen = models.BooleanField(default=False)
    read_write = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.public_key = GenerateAPIKey()
            self.private_key = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for x in range(64))
        super(ApiKey, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ("public_key", "private_key")
