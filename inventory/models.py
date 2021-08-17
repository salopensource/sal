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
    assignmenttype = models.CharField(blank=True, null=True, max_length=255)
    caption = models.CharField(blank=True, null=True, max_length=255)
    description = models.CharField(blank=True, null=True, max_length=255)
    identifyingnumber = models.CharField(blank=True, null=True, max_length=255)
    installdate = models.CharField(blank=True, null=True, max_length=255)
    installdate2 = models.DateTimeField(blank=True, null=True)
    installlocation = models.CharField(blank=True, null=True, max_length=255)
    installstate = models.CharField(blank=True, null=True, max_length=255)
    helplink = models.CharField(blank=True, null=True, max_length=255)
    helptelephone = models.CharField(blank=True, null=True, max_length=255)
    installsource = models.CharField(blank=True, null=True, max_length=255)
    language = models.CharField(blank=True, null=True, max_length=255)
    localpackage = models.CharField(blank=True, null=True, max_length=255)
    packagecache = models.CharField(blank=True, null=True, max_length=255)
    packagecode = models.CharField(blank=True, null=True, max_length=255)
    packagename = models.CharField(blank=True, null=True, max_length=255)
    productid = models.CharField(blank=True, null=True, max_length=255)
    regowner = models.CharField(blank=True, null=True, max_length=255)
    regcompany = models.CharField(blank=True, null=True, max_length=255)
    skunumber = models.CharField(blank=True, null=True, max_length=255)
    transforms = models.CharField(blank=True, null=True, max_length=255)
    urlInfoabout = models.CharField(blank=True, null=True, max_length=255)
    urlupdateInfo = models.CharField(blank=True, null=True, max_length=255)
    vendor = models.CharField(blank=True, null=True, max_length=255)
    wordcount = models.CharField(blank=True, null=True, max_length=255)
    version = models.CharField(blank=True, null=True, max_length=255)
    # Win32 QFE Specifics
    # Win32_QuickFixEngineering class
    # https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-quickfixengineering
    status = models.CharField(blank=True, null=True, max_length=255)
    csname = models.CharField(blank=True, null=True, max_length=255)
    fixcomments = models.CharField(blank=True, null=True, max_length=255)
    hotfixid = models.CharField(blank=True, null=True, max_length=255)
    installedby = models.CharField(blank=True, null=True, max_length=255)
    installedon = models.CharField(blank=True, null=True, max_length=255)
    servicepackIneffect = models.CharField(blank=True, max_length=255)

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
