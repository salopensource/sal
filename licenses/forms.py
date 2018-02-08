from django import forms
from models import *
from django.db.models import Q
from django.contrib.auth.models import User


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = '__all__'
