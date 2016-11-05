from django import forms

from .models import *
from server.models import *

class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass

class SaveSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ('name',)

class SearchRowForm(forms.ModelForm):

    skip_fields = [
        'id',
        'machine_group',
        'report',
        'activity',
        'errors',
        'warnings',
        'install_log',
        'puppet_errors',
        'install_log_hash'
    ]
    search_fields = []
    for f in Machine._meta.fields:
        if f.name not in skip_fields:
            add = (f.name,f.name,)
            search_fields.append(add)

    search_field = ChoiceFieldNoValidation(choices=sorted(search_fields))
    and_or = ChoiceFieldNoValidation(choices=AND_OR_CHOICES)

    def __init__(self, *args, **kwargs):
        self.search_group = kwargs.pop('search_group', None)
        super(SearchRowForm, self).__init__(*args, **kwargs) # Make sure to change "YourForm" to your form's class name
        try:
            search_group_count = self.search_group.searchrow_set.count()
        except:
            search_group_count = 0
        if search_group_count == 0 and self.search_group:
            self.fields['and_or'] = ChoiceFieldNoValidation(
                initial='AND',
                widget=forms.HiddenInput()
            )

    class Meta:
        model = SearchRow
        fields = ('search_models', 'search_field', 'and_or', 'operator','search_term',)
