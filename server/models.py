from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)

    LEVEL_CHOICES = (
        ('SO', 'Stats Only'),
        ('RO', 'Read Only'),
        ('RW', 'Read Write'),
        ('GA', 'Global Admin'),
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='SO')
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class BusinessUnit(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=256)
    users = models.ManyToManyField(User)
    
class MachineGroup(models.Model):
    business_unit = models.ForeignKey(BusinessUnit)
    name = models.CharField(max_length=100)
    manifest = models.CharField(max_length=256)
    
class Machine(models.Model):
    serial = models.CharField(max_length=100)
    hostname = models.CharField(max_length=256)
    operating_system = models.CharField(max_length=256)
    memory = models.CharField(max_length=256)
    munki_version = models.CharField(max_length=256)
    manifest = models.CharField(max_length=256)
    hd_space = models.CharField(max_length=256)
    last_checkin = models.DateTimeField(blank=True,null=True)