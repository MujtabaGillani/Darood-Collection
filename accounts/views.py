from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, RedirectView, TemplateView, View

from .forms import (
    QUICK_ADD_DEFAULT_PASSWORD,
    LoginForm,
    QuickAddUserForm,
    RegisterForm,
)
from .permissions import CanAddDaroodMixin, SuperadminRequiredMixin

User = get_user_model()


class AppLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    # Two weeks, in seconds.
    REMEMBER_AGE = 60 * 60 * 24 * 14

    def form_valid(self, form):
        # "Remember me" keeps the session across browser restarts; otherwise it
        # expires when the browser closes.
        if form.cleaned_data.get('remember'):
            self.request.session.set_expiry(self.REMEMBER_AGE)
        else:
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class AppLogoutView(LogoutView):
    pass


class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Registration successful! Your account is pending approval by an '
            'administrator. You will be able to log in once it is activated.',
        )
        return response


class HomeRedirectView(LoginRequiredMixin, RedirectView):
    """Send each user to the most relevant landing page for their role.

    Anonymous visitors are sent to the login page by ``LoginRequiredMixin``
    before any role check runs.
    """

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_superadmin:
            return str(reverse_lazy('dashboard'))
        if user.is_manager:
            return str(reverse_lazy('darood_overview'))
        return str(reverse_lazy('my_progress'))


class AddSimpleUserView(CanAddDaroodMixin, CreateView):
    """Managers / superadmins quick-add a simple user (username + defaults)."""

    template_name = 'accounts/add_user.html'
    form_class = QuickAddUserForm
    success_url = reverse_lazy('add_darood')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['default_password'] = QUICK_ADD_DEFAULT_PASSWORD
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'User "{self.object.username}" created as a Simple User '
            f'(password: {QUICK_ADD_DEFAULT_PASSWORD}). You can now record their darood.',
        )
        return response


class DashboardView(SuperadminRequiredMixin, TemplateView):
    """Superadmin control centre: manage users + see the graphs."""

    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        from darood.models import DaroodEntry

        ctx = super().get_context_data(**kwargs)
        users = User.objects.all().order_by('-date_joined')

        totals = dict(
            DaroodEntry.objects.filter(status=DaroodEntry.Status.APPROVED)
            .values_list('user_id')
            .annotate(total=Sum('count'))
            .values_list('user_id', 'total')
        )
        for user in users:
            user.darood_total = totals.get(user.pk, 0)

        ctx['users'] = users
        ctx['pending_count'] = users.filter(is_active=False).count()
        ctx['active_count'] = users.filter(is_active=True).count()
        # Only Simple User / Manager are assignable here; Super Admin is not a
        # role the dashboard hands out (superadmins are made via createsuperuser).
        ctx['role_choices'] = [
            choice for choice in User.Role.choices
            if choice[0] != User.Role.SUPERADMIN
        ]
        ctx['grand_total'] = sum(totals.values())
        return ctx


class UpdateUserView(SuperadminRequiredMixin, View):
    """Toggle activation and/or change a user's role from the dashboard."""

    # Roles a superadmin may assign from the dashboard (Super Admin excluded).
    ASSIGNABLE_ROLES = {User.Role.SIMPLE, User.Role.MANAGER}

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        action = request.POST.get('action')

        # Protect super admin accounts: they can't be deactivated or re-roled
        # through this UI (prevents an admin from locking everyone out).
        if target.is_superadmin:
            messages.error(request, 'Super Admin accounts cannot be modified here.')
            return redirect('dashboard')

        if action == 'toggle_active':
            target.is_active = not target.is_active
            target.save(update_fields=['is_active'])
            state = 'activated' if target.is_active else 'deactivated'
            messages.success(request, f'{target.full_name} has been {state}.')

        elif action == 'set_role':
            role = request.POST.get('role')
            if role in self.ASSIGNABLE_ROLES:
                target.role = role
                # A manager also needs Django staff access; a simple user does not.
                target.is_staff = role == User.Role.MANAGER
                target.is_superuser = False
                target.save(update_fields=['role', 'is_superuser', 'is_staff'])
                messages.success(
                    request, f'{target.full_name} is now a {target.get_role_display()}.'
                )
            else:
                messages.error(request, 'You can only assign Simple User or Manager.')
        else:
            messages.error(request, 'Unknown action.')

        return redirect('dashboard')
