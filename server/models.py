from django.db import models
from django.contrib.auth.models import User
import random
import string
import plistlib
from xml.parsers.expat import ExpatError
import base64
import bz2
from datetime import datetime
import watson

def GenerateKey():
    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(128))
    try:
        MachineGroup.objects.get(key=key)
        return GenerateKey()
    except MachineGroup.DoesNotExist:
        return key;

def GenerateAPIKey():
    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(24))
    try:
        ApiKey.objects.get(public_key=key)
        return GenerateAPIKey()
    except ApiKey.DoesNotExist:
        return key;

class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)

    LEVEL_CHOICES = (
        ('SO', 'Stats Only'),
        ('RO', 'Read Only'),
        ('RW', 'Read Write'),
        ('GA', 'Global Admin'),
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='SO')
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
    key = models.CharField(max_length=255, unique=True, blank=True, null=True, editable=False)
    def save(self):
            if not self.id:
                self.key = GenerateKey()
            super(MachineGroup, self).save()
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Machine(models.Model):
    OS_CHOICES = (
        ('Darwin', 'OS X'),
        ('Windows', 'Windows'),
        ('Linux', 'Linux'),
    )
    machine_group = models.ForeignKey(MachineGroup)
    serial = models.CharField(max_length=100, unique=True)
    hostname = models.CharField(max_length=256, null=True, blank=True)
    operating_system = models.CharField(max_length=256, null=True, blank=True)
    memory = models.CharField(max_length=256, null=True, blank=True)
    memory_kb = models.IntegerField(default=0)
    munki_version = models.CharField(max_length=256, null=True, blank=True)
    manifest = models.CharField(max_length=256, null=True, blank=True)
    hd_space = models.CharField(max_length=256, null=True, blank=True)
    hd_total = models.CharField(max_length=256, null=True, blank=True)
    hd_percent = models.CharField(max_length=256, null=True, blank=True)
    console_user = models.CharField(max_length=256, null=True, blank=True)
    machine_model = models.CharField(max_length=256, null=True, blank=True)
    cpu_type = models.CharField(max_length=256, null=True, blank=True)
    cpu_speed = models.CharField(max_length=256, null=True, blank=True)
    os_family = models.CharField(max_length=256, choices=OS_CHOICES, verbose_name="OS Family", default="Darwin")
    last_checkin = models.DateTimeField(blank=True,null=True)
    first_checkin = models.DateTimeField(blank=True,null=True, auto_now_add=True)
    report = models.TextField(editable=True, null=True)
    errors = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    activity = models.TextField(editable=False, null=True, blank=True)
    puppet_version = models.TextField(null=True, blank=True)
    sal_version = models.TextField(null=True, blank=True)
    last_puppet_run = models.DateTimeField(blank=True,null=True)
    puppet_errors = models.IntegerField(default=0)

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
                    return self.b64bz_decode(data)
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

    def get_report(self):
        return self.decode(self.report)

    def get_activity(self):
        return self.decode(self.activity)

    def update_report(self, base64bz2report):
        # Save report.
        try:
            base64bz2report = base64bz2report.replace(" ", "+")
            plist = self.b64bz_decode(base64bz2report)
            #self.report = base64bz2report
            self.report = plistlib.writePlistToString(plist)
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
        super(Machine, self).save()

class Fact(models.Model):
    machine = models.ForeignKey(Machine, related_name='facts')
    fact_name = models.TextField()
    fact_data = models.TextField()
    def __unicode__(self):
        return '%s: %s' % (self.fact_name, self.fact_data)
    class Meta:
        ordering = ['fact_name']

class HistoricalFact(models.Model):
    machine = models.ForeignKey(Machine, related_name='historical_facts')
    fact_name = models.TextField()
    fact_data = models.TextField()
    fact_recorded = models.DateTimeField(db_index=True)
    def __unicode__(self):
        return self.fact_name
    class Meta:
        ordering = ['fact_name', 'fact_recorded']

class Condition(models.Model):
    machine = models.ForeignKey(Machine, related_name='conditions')
    condition_name = models.TextField()
    condition_data = models.TextField()
    def __unicode__(self):
        return self.condition_name
    class Meta:
        ordering = ['condition_name']

class OSQueryResult(models.Model):
    machine = models.ForeignKey(Machine, related_name='osquery_results')
    name = models.CharField(max_length=255)
    hostidentifier = models.CharField(max_length=255, null=True, blank=True)
    unix_time = models.IntegerField()
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['unix_time']

class OSQueryColumn(models.Model):
    osquery_result = models.ForeignKey(OSQueryResult, related_name='osquery_columns')
    column_name = models.TextField()
    column_data = models.TextField(null=True, blank=True)
    action = models.CharField(max_length=255, null=True, blank=True)
    def __unicode__(self):
        return self.column_name

class PendingUpdate(models.Model):
    machine = models.ForeignKey(Machine, related_name='pending_updates')
    update = models.CharField(max_length=255, null=True, blank=True)
    update_version = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    def __unicode__(self):
        return self.update
    class Meta:
        ordering = ['display_name']
        unique_together = ("machine", "update")

class PendingAppleUpdate(models.Model):
    machine = models.ForeignKey(Machine, related_name='pending_apple_updates')
    update = models.CharField(max_length=255, null=True, blank=True)
    update_version = models.CharField(max_length=256, null=True, blank=True)
    display_name = models.CharField(max_length=256, null=True, blank=True)
    def __unicode__(self):
        return unicode(self.update) or u''
    class Meta:
        ordering = ['display_name']
        unique_together = ("machine", "update")

class Plugin(models.Model):
    PLUGIN_TYPES = (
        ('facter', 'Facter'),
        ('munkicondition', 'Munki Condition'),
        ('osquery', 'osquery'),
        ('builtin', 'Built In'),
    )
    name = models.CharField(max_length=255, unique=True)
    order = models.IntegerField()
    type = models.CharField(max_length=255, choices=PLUGIN_TYPES, default='facter')
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['order']

class SalSetting(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    def __unicode__(self):
        return self.name

class ApiKey(models.Model):
    public_key = models.CharField(max_length=255)
    private_key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    has_been_seen = models.BooleanField(default=False)
    def save(self):
            if not self.id:
                self.public_key = GenerateAPIKey()
                self.private_key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(64))
            super(ApiKey, self).save()
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']
        unique_together = ("public_key", "private_key")

watson.register(Machine, exclude=("report", "errors", "warnings",))
watson.register(Fact)
watson.register(Condition)