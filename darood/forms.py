from django import forms
from django.contrib.auth import get_user_model

from .models import DaroodEntry

User = get_user_model()


def addable_users_queryset(request_user):
    """Which users a given user is allowed to log darood for.

    * Super admin  -> everyone
    * Manager      -> simple users and managers (not super admins)
    """
    qs = User.objects.filter(is_active=True).order_by('first_name', 'username')
    if request_user.is_superadmin:
        return qs
    return qs.filter(role__in=[User.Role.SIMPLE, User.Role.MANAGER])


class AddDaroodForm(forms.ModelForm):
    """Record darood for a searched-and-selected user on a chosen date.

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
        if request_user is not None:
            self.fields['user'].queryset = addable_users_queryset(request_user)
        self.fields['user'].error_messages['required'] = 'Please search and select a user.'
