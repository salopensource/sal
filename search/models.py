from __future__ import unicode_literals

import django.utils.timezone
from django.db import models
from django.contrib.auth.models import User
from current_user import get_current_user
from server.models import *
# Create your models here.

AND_OR_CHOICES = (
    ('AND', 'AND'),
    ('OR', 'OR'),
)


class SavedSearch(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    save_search = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, default=get_current_user)

    def __getattribute__(self, name):
        attr = models.Model.__getattribute__(self, name)
        now = django.utils.timezone.now()
        if name == 'name' and not attr:
            return 'Unsaved Search %s' % str(now)
        return attr

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SearchGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    saved_search = models.ForeignKey(SavedSearch)
    and_or = models.CharField(choices=AND_OR_CHOICES, default='AND', max_length=3)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']


class SearchRow(models.Model):
    SEARCH_MODEL_CHOICES = (
        ('Machine', 'Machine'),
        ('Facter', 'Facter'),
        ('Condition', 'Condition'),
        ('External Script', 'External Script'),
        ('Application Inventory', 'Application Inventory'),
        ('Application Version', 'Application Version'),
        ('Profile', 'Profile'),
        ('Profile Payload', 'Profile Payload'),
    )
    SEARCH_OPERATOR_CHOICES = (
        ('Contains', 'Contains'),
        ('=', '='),
        ('!=', '!='),
        ('<', '<'),
        ('<=', '<='),
        ('>', '>'),
        ('>=', '>='),
    )
    id = models.BigAutoField(primary_key=True)
    search_group = models.ForeignKey(SearchGroup)
    search_models = models.CharField(choices=SEARCH_MODEL_CHOICES,
                                     default='AND', max_length=254, verbose_name='Search item')
    search_field = models.CharField(max_length=254)
    and_or = models.CharField(choices=AND_OR_CHOICES, default='AND',
                              max_length=3, verbose_name='AND / OR')
    operator = models.CharField(choices=SEARCH_OPERATOR_CHOICES, default='Contains', max_length=9)
    search_term = models.CharField(max_length=254)
    position = models.IntegerField()

    class Meta:
        ordering = ['position']


class SearchFieldCache(models.Model):
    SEARCH_MODEL_CHOICES = (
        ('Machine', 'Machine'),
        ('Facter', 'Facter'),
        ('Condition', 'Condition'),
        ('External Script', 'External Script'),
        ('Application Inventory', 'Application Inventory'),
        ('Application Version', 'Application Version'),
    )
    id = models.BigAutoField(primary_key=True)
    search_model = models.CharField(choices=SEARCH_MODEL_CHOICES,
                                    default='AND', max_length=254, verbose_name='Search item')
    search_field = models.CharField(max_length=254)

    def __unicode__(self):
        return '%s: %s' % (self.search_model, self.search_field)


class SearchCache(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine = models.ForeignKey(Machine)
    search_item = models.TextField()
