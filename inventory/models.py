from django.db import models
from server.models import *
import watson
# Create your models here.

class Inventory(models.Model):
    machine = models.ForeignKey(Machine)
    datestamp = models.DateTimeField(auto_now=True)
    sha256hash = models.CharField(max_length=64)
    class Meta:
        ordering = ['datestamp']


class InventoryItem(models.Model):
    machine = models.ForeignKey(Machine)
    name = models.CharField(db_index=True, max_length=255)
    version = models.CharField(db_index=True, max_length=32)
    bundleid = models.CharField(db_index=True, max_length=255)
    bundlename = models.CharField(db_index=True, max_length=255)
    path = models.TextField()
    class Meta:
        ordering = ['name', '-version']

watson.register(InventoryItem)