from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.utils.translation import gettext as _

from .models import Person


class PersonCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and password.
    """

    def __init__(self, *args, **kargs):
        super(PersonCreationForm, self).__init__(*args, **kargs)

    class Meta:
        model = Person
        fields = ("email",)


class PersonChangeForm(UserChangeForm):
    """
    A form for updating users. Includes all the fields on the user, but replaces the password
    field with admin's password hash display field.
    """

    def __init__(self, *args, **kargs):
        super(PersonChangeForm, self).__init__(*args, **kargs)

    class Meta:
        model = Person
        exclude = ('',)


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Please enter a password.')
            }
        )
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Please confirm password.')
            }
        )
    )
