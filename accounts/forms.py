from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class BootstrapMixin:
    """Add Bootstrap classes to every visible field's widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = 'form-check-input' if isinstance(widget, forms.CheckboxInput) else 'form-control'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {css}'.strip()


class RegisterForm(BootstrapMixin, UserCreationForm):
    """Public sign-up: username (unique), first/last name, password twice.

    ``UserCreationForm`` already gives us the two password fields plus the
    "passwords must match" validation, so we just add the name fields.
    """

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # New accounts start inactive; a superadmin activates them later.
        user.is_active = False
        user.role = User.Role.SIMPLE
        if commit:
            user.save()
        return user


class LoginForm(BootstrapMixin, AuthenticationForm):
    """Standard username/password login with Bootstrap styling."""


class UserManagementForm(BootstrapMixin, forms.ModelForm):
    """Used by superadmins on the dashboard to toggle activation & role."""

    class Meta:
        model = User
        fields = ('is_active', 'role')
