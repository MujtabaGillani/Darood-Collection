from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, RedirectView, TemplateView, View

from .forms import LoginForm, RegisterForm
from .permissions import SuperadminRequiredMixin

User = get_user_model()


class AppLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


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


class HomeRedirectView(RedirectView):
    """Send each user to the most relevant landing page for their role."""

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_superadmin:
            return str(reverse_lazy('dashboard'))
        if user.is_manager:
            return str(reverse_lazy('darood_overview'))
        return str(reverse_lazy('my_progress'))


class DashboardView(SuperadminRequiredMixin, TemplateView):
    """Superadmin control centre: manage users + see the graphs."""

    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        from darood.models import DaroodEntry

        ctx = super().get_context_data(**kwargs)
        users = User.objects.all().order_by('-date_joined')

        totals = dict(
            DaroodEntry.objects.values_list('user_id')
            .annotate(total=Sum('count'))
            .values_list('user_id', 'total')
        )
        for user in users:
            user.darood_total = totals.get(user.pk, 0)

        ctx['users'] = users
        ctx['pending_count'] = users.filter(is_active=False).count()
        ctx['active_count'] = users.filter(is_active=True).count()
        ctx['role_choices'] = User.Role.choices
        ctx['grand_total'] = sum(totals.values())
        return ctx


class UpdateUserView(SuperadminRequiredMixin, View):
    """Toggle activation and/or change a user's role from the dashboard."""

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        action = request.POST.get('action')

        if action == 'toggle_active':
            target.is_active = not target.is_active
            target.save(update_fields=['is_active'])
            state = 'activated' if target.is_active else 'deactivated'
            messages.success(request, f'{target.full_name} has been {state}.')

        elif action == 'set_role':
            role = request.POST.get('role')
            valid = {choice[0] for choice in User.Role.choices}
            if role in valid:
                target.role = role
                # Keep Django's superuser/staff flags in sync with the role so
                # a promoted superadmin also gets Django admin-site access.
                target.is_superuser = role == User.Role.SUPERADMIN
                target.is_staff = role in (User.Role.SUPERADMIN, User.Role.MANAGER)
                target.save(update_fields=['role', 'is_superuser', 'is_staff'])
                messages.success(
                    request, f'{target.full_name} is now a {target.get_role_display()}.'
                )
            else:
                messages.error(request, 'Invalid role selected.')
        else:
            messages.error(request, 'Unknown action.')

        return redirect('dashboard')
