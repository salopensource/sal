from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

from licenses.models import *


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = '__all__'
