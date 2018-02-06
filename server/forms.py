from django import forms
from models import *
from django.db.models import Q
from django.contrib.auth.models import User

User.full_name = property(lambda u: u"%s %s" % (u.first_name, u.last_name))


def user_new_unicode(self):
    return self.username if self.get_full_name() == "" else self.get_full_name()


# Replace the __unicode__ method in the User class with out new implementation
User.__unicode__ = user_new_unicode

LEVEL_CHOICES = (
    ('RO', 'Read Only'),
    ('RW', 'Read Write'),
    ('GA', 'Global Admin'),
)


class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        widgets = {'users': forms.CheckboxSelectMultiple}
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(BusinessUnitForm, self).__init__(*args, **kwargs)
        self.fields['users'].help_text = ''
        self.fields['users'].queryset = User.objects.order_by(
            'username').filter(~Q(userprofile__level='GA'))


class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        fields = ('name', 'read_write')


class EditBusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = ('name',)


class EditUserBusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        widgets = {'users': forms.CheckboxSelectMultiple}
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EditUserBusinessUnitForm, self).__init__(*args, **kwargs)

        self.fields['users'].help_text = ''
        self.fields['users'].queryset = User.objects.order_by(
            'username').filter(~Q(userprofile__level='GA'))


class NewMachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ('serial',)


class MachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)


class EditMachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ('name',)


class NewUserForm(forms.Form):
    """
    Form for registering a new account.
    """
    username = forms.CharField(widget=forms.TextInput(), label="Username")
    password1 = forms.CharField(widget=forms.PasswordInput(),
                                label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(),
                                label="Password (again)")

    user_level = forms.ChoiceField(choices=LEVEL_CHOICES)

    def clean_username(self):  # check if username dos not exist before
        if len(self.cleaned_data['username']) > 30:
            raise forms.ValidationError("Username must be under 30 characters")
        try:
            User.objects.get(username=self.cleaned_data['username'])  # get user from user model
        except User.DoesNotExist:
            return self.cleaned_data['username']

        raise forms.ValidationError("Username already exists")

    def clean(self):  # check if password 1 and password2 match each other
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:  # check if both pass first validation
            # check if they match each other
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError("Passwords must match")

        return self.cleaned_data

    def save(self):  # create new user
        new_user = User.objects.create_user(username=self.cleaned_data['username'],
                                            password=self.cleaned_data['password1'],
                                            )
        new_user.userprofile.level = self.cleaned_data['user_level']
        new_user.userprofile.save()
        return new_user


class SettingsHistoricalDataForm(forms.Form):
    days = forms.IntegerField(label='Data retention days', required=True)


class EditLDAPUserForm(forms.Form):
    """
    Form for editing a LDAP user account.
    """
    user_id = forms.CharField(widget=forms.HiddenInput())

    user_level = forms.ChoiceField(choices=LEVEL_CHOICES)

    def clean(self):  # check if password 1 and password2 match each other
        return self.cleaned_data

    def save(self):  # create new user
        the_user = User.objects.get(id=int(self.cleaned_data['user_id']))
        the_user.save()
        return the_user


class EditUserForm(forms.Form):
    """
    Form for editing a user account.
    """
    user_id = forms.CharField(widget=forms.HiddenInput())

    password1 = forms.CharField(widget=forms.PasswordInput(),
                                label="Password", required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(),
                                label="Password (again)", required=False)

    user_level = forms.ChoiceField(choices=LEVEL_CHOICES)

    def clean(self):  # check if password 1 and password2 match each other
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:  # check if both pass first validation
            # check if they match each other
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError("Passwords must match")

        return self.cleaned_data

    def save(self):  # create new user
        the_user = User.objects.get(id=int(self.cleaned_data['user_id']))
        if self.cleaned_data['password1'] != "":
            the_user.set_password(self.cleaned_data['password1'])
            the_user.save()
        return the_user


class UserToBUForm(forms.ModelForm):
    #cats = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple(),required=True)
    class Meta:
        model = User
        fields = '__all__'
