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
    """Username/password login with a "remember me" option."""

    remember = forms.BooleanField(required=False, initial=False, label='Remember me')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Help the browser's password manager offer to save / autofill.
        self.fields['username'].widget.attrs.update({'autocomplete': 'username', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})


class UserManagementForm(BootstrapMixin, forms.ModelForm):
    """Used by superadmins on the dashboard to toggle activation & role."""

    class Meta:
        model = User
        fields = ('is_active', 'role')


# Default password given to users quick-added by a manager / superadmin.
QUICK_ADD_DEFAULT_PASSWORD = 'test3450'


class QuickAddUserForm(BootstrapMixin, forms.ModelForm):
    """Managers / superadmins quickly create a simple user by username.

    Name is optional; the account is created active as a Simple User with a
    known default password so darood can be recorded for them immediately.
    """

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['first_name'].label = 'First name (optional)'
        self.fields['last_name'].label = 'Last name (optional)'
        self.fields['username'].widget.attrs['autofocus'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.SIMPLE
        user.is_active = True            # active so they appear in the search
        user.set_password(QUICK_ADD_DEFAULT_PASSWORD)
        if commit:
            user.save()
        return user
