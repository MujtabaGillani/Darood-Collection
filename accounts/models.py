from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Project user.

    Extends Django's built-in user (which already provides ``username``,
    ``first_name``, ``last_name``, ``password`` and ``is_active``) with a
    ``role`` so we can distinguish simple users, managers and superadmins.

    New accounts are created **inactive** (``is_active=False``) and stay that
    way until a superadmin approves them from the dashboard.
    """

    class Role(models.TextChoices):
        SIMPLE = 'simple', _('Simple User')
        MANAGER = 'manager', _('Manager')
        SUPERADMIN = 'superadmin', _('Super Admin')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SIMPLE,
    )

    # --- convenience helpers used across views / templates ----------------
    @property
    def is_superadmin(self):
        # A Django superuser is always treated as a super admin regardless of
        # the stored role, so the first `createsuperuser` account just works.
        return self.is_superuser or self.role == self.Role.SUPERADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def can_add_darood(self):
        """Managers and superadmins may record darood for others."""
        return self.is_manager or self.is_superadmin

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    def __str__(self):
        label = self.get_full_name()
        return f'{self.username} ({label})' if label else self.username
