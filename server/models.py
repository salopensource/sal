import plistlib
import random
import string
from datetime import datetime
from xml.parsers.expat import ExpatError

import pytz
from dateutil.parser import parse

from django.contrib.auth.models import User
from django.db import models

from utils import text_utils


OS_CHOICES = (
    ('Darwin', 'macOS'),
    ('Windows', 'Windows'),
    ('Linux', 'Linux'),
    ('ChromeOS', 'Chrome OS'),
)

REPORT_CHOICES = (
    ('base64', 'base64'),
    ('base64bz2', 'base64bz2'),
    ('bz2', 'bz2'),
)


class ProfileLevel():
    stats_only = 'SO'
    read_only = 'RO'
    read_write = 'RW'
    global_admin = 'GA'


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

    def __str__(self):
        return self.user.username


User.userprofile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class BusinessUnit(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def display_name(cls):
        return text_utils.class_to_title(cls.__name__)

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

    def __str__(self):
        return self.name

    @classmethod
    def display_name(cls):
        return text_utils.class_to_title(cls.__name__)

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
    errors = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    activity = models.BooleanField(editable=True, default=False)
    puppet_version = models.CharField(db_index=True, null=True, blank=True, max_length=256)
    sal_version = models.CharField(db_index=True, null=True, blank=True, max_length=255)
    last_puppet_run = models.DateTimeField(db_index=True, blank=True, null=True)
    puppet_errors = models.IntegerField(db_index=True, default=0)
    deployed = models.BooleanField(default=True)
    broken_client = models.BooleanField(default=False)

    objects = models.Manager()  # The default manager.
    deployed_objects = DeployedManager()

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Machine._meta.fields]

    def get_report(self):
        return text_utils.submission_plist_loads(self.report)

    def __str__(self):
        if self.hostname:
            return self.hostname
        else:
            return self.serial

    @classmethod
    def display_name(cls):
        return text_utils.class_to_title(cls.__name__)

    class Meta:
        ordering = ['hostname']


GROUP_NAMES = {
    'all': None,
    'machine_group': MachineGroup,
    'business_unit': BusinessUnit,
    'machine': Machine}


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

    def __str__(self):
        return "%s: %s %s" % (self.machine, self.name, self.version)

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

    def __str__(self):
        return "%s: %s %s %s %s" % (
            self.update_history.machine,
            self.update_history.name,
            self.update_history.version,
            self.status, self.recorded
        )

    class Meta:
        ordering = ['-recorded']
        unique_together = (("update_history", "recorded", "status"),)


class Fact(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='facts')
    fact_name = models.TextField()
    fact_data = models.TextField()

    def __str__(self):
        return '%s: %s' % (self.fact_name, self.fact_data)

    class Meta:
        ordering = ['fact_name']


class HistoricalFact(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='historical_facts')
    fact_name = models.CharField(max_length=255)
    fact_data = models.TextField()
    fact_recorded = models.DateTimeField()

    def __str__(self):
        return self.fact_name

    class Meta:
        ordering = ['fact_name', 'fact_recorded']


class Condition(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='conditions')
    condition_name = models.CharField(max_length=255)
    condition_data = models.TextField()

    def __str__(self):
        return self.condition_name

    class Meta:
        ordering = ['condition_name']


class PluginScriptSubmission(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine)
    plugin = models.CharField(max_length=255)
    historical = models.BooleanField(default=False)
    recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: %s' % (self.machine, self.plugin)

    class Meta:
        ordering = ['recorded', 'plugin']


class PluginScriptRow(models.Model):
    id = models.BigAutoField(primary_key=True)
    submission = models.ForeignKey(PluginScriptSubmission)
    pluginscript_name = models.TextField()
    pluginscript_data = models.TextField(blank=True, null=True)
    pluginscript_data_string = models.TextField(blank=True, null=True)
    pluginscript_data_int = models.IntegerField(default=0)
    pluginscript_data_date = models.DateTimeField(blank=True, null=True)
    submission_and_script_name = models.TextField()

    def save(self):
        try:
            self.pluginscript_data_int = int(self.pluginscript_data)
        except (ValueError, TypeError):
            self.pluginscript_data_int = 0

        self.pluginscript_data_string = str(self.pluginscript_data)

        try:
            date_data = parse(self.pluginscript_data)
            if not date_data.tzinfo:
                date_data = date_data.replace(tzinfo=pytz.UTC)
            self.pluginscript_data_date = date_data
        except ValueError:
            # Try converting it to an int if we're here
            try:
                if int(self.pluginscript_data) != 0:

                    try:
                        self.pluginscript_data_date = datetime.fromtimestamp(
                            int(self.pluginscript_data), tz=pytz.UTC)
                    except (ValueError, TypeError):
                        self.pluginscript_data_date = None
                else:
                    self.pluginscript_data_date = None
            except (ValueError, TypeError):
                self.pluginscript_data_date = None

        super(PluginScriptRow, self).save()

    def __str__(self):
        return '%s: %s' % (self.pluginscript_name, self.pluginscript_data)

    class Meta:
        ordering = ['pluginscript_name']


class PendingUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='pending_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.update

    class Meta:
        ordering = ['display_name']


class InstalledUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='installed_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    installed = models.BooleanField()

    def __str__(self):
        return self.update

    class Meta:
        ordering = ['display_name']
        unique_together = ("machine", "update", "update_version")


class PendingAppleUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, related_name='pending_apple_updates')
    update = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    update_version = models.CharField(max_length=256, null=True, blank=True)
    display_name = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.update or ''

    class Meta:
        ordering = ['display_name']


class Plugin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    order = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


class MachineDetailPlugin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    order = models.IntegerField()

    def __str_(self):
        return self.name

    class Meta:
        ordering = ['order']


class Report(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SalSetting(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.name


class ApiKey(models.Model):
    public_key = models.CharField(max_length=255)
    private_key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    has_been_seen = models.BooleanField(default=False)
    read_write = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.public_key = GenerateAPIKey()
            self.private_key = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for x in range(64))
        super(ApiKey, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ("public_key", "private_key")


class FriendlyNameCache(models.Model):
    serial_stub = models.CharField(max_length=5)
    friendly_name = models.CharField(max_length=255)
