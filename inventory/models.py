from django.db import models
from server.models import *
import watson


class Application(models.Model):
    name = models.CharField(db_index=True, max_length=255)
    bundleid = models.CharField(db_index=True, max_length=255)
    bundlename = models.CharField(db_index=True, max_length=255)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Inventory(models.Model):
    machine = models.ForeignKey(Machine)
    datestamp = models.DateTimeField(auto_now=True)
    sha256hash = models.CharField(max_length=64)

    class Meta:
        ordering = ['datestamp']


class InventoryItem(models.Model):
    machine = models.ForeignKey(Machine)
    application = models.ForeignKey(Application)
    version = models.CharField(db_index=True, max_length=32)
    path = models.TextField()


watson.register(InventoryItem)