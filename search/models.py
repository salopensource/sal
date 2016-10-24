from __future__ import unicode_literals

import django.utils.timezone
from django.db import models
from django.contrib.auth.models import User
from current_user import get_current_user

# Create your models here.

AND_OR_CHOICES = (
    ('AND', 'AND'),
    ('OR', 'OR'),
)
class SavedSearch(models.Model):
    now = django.utils.timezone.now()
    default = 'Unsaved Search %s' % str(now)
    name = models.CharField(max_length=100, default=default)
    created = models.DateTimeField(auto_now_add=True)
    save_search = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, default=get_current_user)

    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

class SearchGroup(models.Model):
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
    )
    SEARCH_OPERATOR_CHOICES = (
        ('Contains', 'Contains'),
        ('=','='),
        ('!=', '!='),
        ('<','<'),
        ('<=','<='),
        ('>','>'),
        ('>=', '>='),
    )
    search_group = models.ForeignKey(SearchGroup)
    search_models = models.CharField(choices=SEARCH_MODEL_CHOICES, default='AND', max_length=254, verbose_name='Search item')
    search_field = models.CharField(max_length=254)
    and_or = models.CharField(choices=AND_OR_CHOICES, default='AND', max_length=3, verbose_name='AND / OR')
    operator = models.CharField(choices=SEARCH_OPERATOR_CHOICES, default='Contains', max_length=9)
    search_term = models.CharField(max_length=254)
    position = models.IntegerField()
    class Meta:
        ordering = ['position']
