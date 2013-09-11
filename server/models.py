from django.db import models
from django.contrib.auth.models import User
import random
import string

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
    serial = models.CharField(max_length=100)
    hostname = models.CharField(max_length=256)
    operating_system = models.CharField(max_length=256)
    memory = models.CharField(max_length=256)
    munki_version = models.CharField(max_length=256)
    manifest = models.CharField(max_length=256)
    hd_space = models.CharField(max_length=256)
    last_checkin = models.DateTimeField(blank=True,null=True)
    def __unicode__(self):
        return self.hostname