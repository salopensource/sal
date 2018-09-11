from django.db import models
from server.models import *


class Application(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(db_index=True, max_length=255)
    bundleid = models.CharField(db_index=True, max_length=255)
    bundlename = models.CharField(db_index=True, max_length=255)

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'bundleid', 'bundlename'))

    def __unicode__(self):
        return self.name


class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.OneToOneField(Machine)
    datestamp = models.DateTimeField(auto_now=True)
    sha256hash = models.CharField(max_length=64)
    inventory_str = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['datestamp']


class InventoryItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine)
    application = models.ForeignKey(Application)
    version = models.CharField(db_index=True, max_length=64)
    path = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['application', '-version']
