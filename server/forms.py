from django import forms
from models import *

class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        # fields = ('name','prefix','domain',)
        
class MachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)

class EditMachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)