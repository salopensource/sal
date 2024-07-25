from django.db import models
from server.models import *


class Catalog(models.Model):
    id = models.AutoField(primary_key=True)
    machine_group = models.ForeignKey(MachineGroup, on_delete=models.CASCADE)
    content = models.TextField()
    name = models.CharField(max_length=253)
    sha256hash = models.CharField(max_length=64)

    class Meta:
        ordering = ['name', 'machine_group']
