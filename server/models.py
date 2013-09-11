from django.db import models
from django.contrib.auth.models import User
import random
import string
import plistlib
from xml.parsers.expat import ExpatError
import base64
import bz2
from datetime import datetime

# def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
# ...    return ''.join(random.choice(chars) for x in range(size))
def GenerateKey():
    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(128))
    try:
        BusinessUnit.objects.get(key=key)
        return GenerateKey()
    except BusinessUnit.DoesNotExist:
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
User.userprofile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class BusinessUnit(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=256, unique=True, blank=True, null=True, editable=False)
    users = models.ManyToManyField(User)
    
    def save(self):
            if not self.id:
                self.key = GenerateKey()
            super(BusinessUnit, self).save()
            
    def __unicode__(self):
        return self.name

class MachineGroup(models.Model):
    business_unit = models.ForeignKey(BusinessUnit)
    name = models.CharField(max_length=100)
    manifest = models.CharField(max_length=256)
    def __unicode__(self):
        return self.name
    
class Machine(models.Model):
    machine_group = models.ForeignKey(MachineGroup)
    serial = models.CharField(max_length=100, unique=True)
    hostname = models.CharField(max_length=256, null=True)
    operating_system = models.CharField(max_length=256)
    memory = models.CharField(max_length=256)
    munki_version = models.CharField(max_length=256)
    manifest = models.CharField(max_length=256)
    hd_space = models.CharField(max_length=256)
    console_user = models.CharField(max_length=256)
    last_checkin = models.DateTimeField(blank=True,null=True)
    report = models.TextField(editable=False, null=True)
    errors = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    activity = models.TextField(editable=False, null=True)
    
    def hostname(self):
        return self.machine.hostname
        
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
            return self.serial