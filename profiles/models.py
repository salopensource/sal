from django.db import models
from server.models import *


class Profile(models.Model):
    machine = models.ForeignKey(Machine)
    identifier = models.CharField(db_index=True, max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    install_data = models.DateTimeField()
    organization = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    verification_state = models.CharField(max_length=255)

    class Meta:
        ordering = ['display_name']

    def __unicode__(self):
        return self.display_name


class Payload(models.Model):
    profile = models.ForeignKey(Profile)
    type = models.CharField(max_length=255)
    identifier = models.CharField(db_index=True, max_length=255)
    uuid = models.CharField(max_length=255)

    class Meta:
        ordering = ['identifier']

    def __unicode__(self):
        return '{} {}'.format(self.identifier, self.uuid)
