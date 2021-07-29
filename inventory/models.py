from django.db import models
from server.models import *


class Application(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(db_index=True, max_length=255)
    bundleid = models.CharField(db_index=True, max_length=255)
    bundlename = models.CharField(db_index=True, max_length=255)

    # Win32_Product Specifics
    # Windows Win32_Product Class
    # https://docs.microsoft.com/en-us/previous-versions/windows/desktop/legacy/aa394378(v=vs.85)
    AssignmentType = models.CharField(blank=True, null=True, max_length=255)
    Caption = models.CharField(blank=True, null=True, max_length=255)
    Description = models.CharField(blank=True, null=True, max_length=255)
    IdentifyingNumber = models.CharField(blank=True, null=True, max_length=255)
    InstallDate = models.CharField(blank=True, null=True, max_length=255)
    InstallDate2 = models.DateTimeField(blank=True, null=True)
    InstallLocation = models.CharField(blank=True, null=True, max_length=255)
    InstallState = models.CharField(blank=True, null=True, max_length=255)
    HelpLink = models.CharField(blank=True, null=True, max_length=255)
    HelpTelephone = models.CharField(blank=True, null=True, max_length=255)
    InstallSource = models.CharField(blank=True, null=True, max_length=255)
    Language = models.CharField(blank=True, null=True, max_length=255)
    LocalPackage = models.CharField(blank=True, null=True, max_length=255)
    PackageCache = models.CharField(blank=True, null=True, max_length=255)
    PackageCode = models.CharField(blank=True, null=True, max_length=255)
    PackageName = models.CharField(blank=True, null=True, max_length=255)
    ProductID = models.CharField(blank=True, null=True, max_length=255)
    RegOwner = models.CharField(blank=True, null=True, max_length=255)
    RegCompany = models.CharField(blank=True, null=True, max_length=255)
    SKUNumber = models.CharField(blank=True, null=True, max_length=255)
    Transforms = models.CharField(blank=True, null=True, max_length=255)
    URLInfoAbout = models.CharField(blank=True, null=True, max_length=255)
    URLUpdateInfo = models.CharField(blank=True, null=True, max_length=255)
    Vendor = models.CharField(blank=True, null=True, max_length=255)
    WordCount = models.CharField(blank=True, null=True, max_length=255)
    Version = models.CharField(blank=True, null=True, max_length=255)
    # Win32 QFE Specifics
    # Win32_QuickFixEngineering class
    # https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-quickfixengineering
    Status = models.CharField(blank=True, null=True, max_length=255)
    CSName = models.CharField(blank=True, null=True, max_length=255)
    FixComments = models.CharField(blank=True, null=True, max_length=255)
    HotFixID = models.CharField(blank=True, null=True, max_length=255)
    InstalledBy = models.CharField(blank=True, null=True, max_length=255)
    InstalledOn = models.CharField(blank=True, null=True, max_length=255)
    ServicePackInEffect = models.CharField(blank=True, max_length=255)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'bundleid', 'bundlename')

    def __str__(self):
        return self.name


class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE)
    datestamp = models.DateTimeField(auto_now=True)
    sha256hash = models.CharField(max_length=64)

    class Meta:
        ordering = ['datestamp']


class InventoryItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    version = models.CharField(db_index=True, max_length=64)
    path = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['application', '-version']
