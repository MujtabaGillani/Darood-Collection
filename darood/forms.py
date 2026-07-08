from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import DaroodEntry

User = get_user_model()


class NoFutureDateMixin:
    """Reject darood entries dated after today — you can't recite ahead."""

    def clean_date(self):
        entry_date = self.cleaned_data.get('date')
        if entry_date and entry_date > timezone.localdate():
            raise forms.ValidationError("The date can't be in the future.")
        return entry_date


def addable_users_queryset(request_user):
    """Which users a given user is allowed to log darood for (manager add-flow).

    * Super admin  -> everyone
    * Manager      -> simple users and managers (not super admins)
    """
    qs = User.objects.filter(is_active=True).order_by('first_name', 'username')
    if request_user.is_superadmin:
        return qs
    return qs.filter(role__in=[User.Role.SIMPLE, User.Role.MANAGER])


def managers_queryset():
    """Active managers a simple user may submit their darood to."""
    return User.objects.filter(
        is_active=True, role=User.Role.MANAGER
    ).order_by('first_name', 'username')


class AddDaroodForm(NoFutureDateMixin, forms.ModelForm):
    """Manager / superadmin records darood for a searched user (auto-approved).

    The template renders a search box (autocomplete) that populates the hidden
    ``user`` field with the selected user's id; the queryset here enforces —
    server-side — that the selection is one the requester is allowed to pick.
    """

    class Meta:
        model = DaroodEntry
        fields = ('user', 'date', 'count')
        widgets = {
            'user': forms.HiddenInput(),
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d',
            ),
            'count': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1, 'placeholder': 'e.g. 500'}
            ),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].widget.attrs['max'] = timezone.localdate().isoformat()
        if request_user is not None:
            self.fields['user'].queryset = addable_users_queryset(request_user)
        self.fields['user'].error_messages['required'] = 'Please search and select a user.'


class SubmitDaroodForm(NoFutureDateMixin, forms.ModelForm):
    """A simple user submits their own darood to a chosen manager (pending)."""

    class Meta:
        model = DaroodEntry
        fields = ('manager', 'date', 'count')
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d',
            ),
            'count': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1, 'placeholder': 'e.g. 500'}
            ),
        }
        labels = {'manager': 'Send to manager'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].widget.attrs['max'] = timezone.localdate().isoformat()
        self.fields['manager'].queryset = managers_queryset()
        self.fields['manager'].required = True
        self.fields['manager'].empty_label = 'Select your manager…'
        self.fields['manager'].widget.attrs['class'] = 'form-select'
