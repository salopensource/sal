from django import forms
from models import *

class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        widgets = {'users': forms.CheckboxSelectMultiple}
    def __init__(self, *args, **kwargs):
        super(BusinessUnitForm, self).__init__(*args, **kwargs)
        self.fields['users'].help_text = ''
        
class MachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)

class EditMachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)

# class UserToBU(forms.ModelForm):
#     bus = forms.ModelMultipleChoiceField(
#         queryset=Entry.objects.all(),
#         widget=forms.CheckboxSelectMultiple)

#     class Meta:
#         model = BusinessUnit

#     def __init__(self, *args, **kwargs):
#         super(BlogForm, self).__init__(*args, **kwargs)
#         if self.instance:
#             entries = Entry.objects.filter(blog=blog)
#             self.fields['entries'].queryset = entries