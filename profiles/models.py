from django.db import models
from server.models import Machine


class Profile(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    identifier = models.CharField(db_index=True, max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    install_date = models.DateTimeField()
    organization = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    verification_state = models.CharField(max_length=255)

    class Meta:
        ordering = ['display_name']

    def __str__(self):
        return self.display_name

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Profile._meta.fields]


class Payload(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    payload_type = models.CharField(max_length=255)
    identifier = models.CharField(db_index=True, max_length=255)
    uuid = models.CharField(max_length=255)

    class Meta:
        ordering = ['identifier']

    def __str__(self):
        return '{} {}'.format(self.identifier, self.uuid)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Payload._meta.fields]
