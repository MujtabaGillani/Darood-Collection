"""Reusable access-control mixins for class-based views."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class SuperadminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only super admins (role or Django superuser) may access the view."""

    def test_func(self):
        return self.request.user.is_superadmin


class CanAddDaroodMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Managers and super admins may record darood for others."""

    def test_func(self):
        return self.request.user.can_add_darood
