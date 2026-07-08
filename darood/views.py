from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from accounts.permissions import CanAddDaroodMixin
from .forms import AddDaroodForm, addable_users_queryset
from .models import DaroodEntry
from .services import (
    PERIODS,
    filter_by_period,
    time_series,
    total_count,
)

User = get_user_model()


def _current_period(request):
    period = request.GET.get('period', 'month')
    return period if period in {k for k, _ in PERIODS} else 'month'


class AddDaroodView(CanAddDaroodMixin, CreateView):
    """Managers / superadmins record a darood count for a searched user."""

    model = DaroodEntry
    form_class = AddDaroodForm
    template_name = 'darood/add.html'
    success_url = reverse_lazy('add_darood')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def get_initial(self):
        return {'date': timezone.localdate()}

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        response = super().form_valid(form)
        entry = form.instance
        messages.success(
            self.request,
            f'Recorded {entry.count} darood for {entry.user.full_name} '
            f'on {entry.date:%d %b %Y}.',
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent'] = (
            DaroodEntry.objects.select_related('user')
            .filter(recorded_by=self.request.user)[:10]
        )
        return ctx


class UserSearchAPI(CanAddDaroodMixin, TemplateView):
    """JSON autocomplete for the add-darood search box.

    Returns users (scoped to what the requester may log for) matching the
    ``q`` query against username / first name / last name.
    """

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        qs = addable_users_queryset(request.user)
        if q:
            from django.db.models import Q

            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
        results = [
            {
                'id': u.pk,
                'text': u.full_name,
                'username': u.username,
                'role': u.get_role_display(),
            }
            for u in qs[:15]
        ]
        return JsonResponse({'results': results})


class DaroodOverviewView(LoginRequiredMixin, TemplateView):
    """Aggregate view of ALL users' darood for a period (managers/superadmin).

    Simple users are redirected to their own progress page instead.
    """

    template_name = 'darood/overview.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.can_add_darood:
            from django.shortcuts import redirect

            return redirect('my_progress')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.db.models import Sum

        ctx = super().get_context_data(**kwargs)
        period = _current_period(self.request)
        entries = filter_by_period(DaroodEntry.objects.all(), period)

        ctx['period'] = period
        ctx['periods'] = PERIODS
        ctx['total'] = total_count(entries)
        ctx['entry_count'] = entries.count()
        ctx['contributor_count'] = entries.values('user').distinct().count()
        ctx['leaderboard'] = (
            entries.values('user__username', 'user__first_name', 'user__last_name')
            .annotate(total=Sum('count'))
            .order_by('-total')[:10]
        )
        ctx['recent'] = entries.select_related('user', 'recorded_by')[:20]
        return ctx


class MyProgressView(LoginRequiredMixin, TemplateView):
    """A user's own darood progress with a period filter + chart."""

    template_name = 'darood/my_progress.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = _current_period(self.request)
        entries = filter_by_period(
            DaroodEntry.objects.filter(user=self.request.user), period
        )
        ctx['period'] = period
        ctx['periods'] = PERIODS
        ctx['total'] = total_count(entries)
        ctx['entry_count'] = entries.count()
        ctx['recent'] = entries.select_related('recorded_by')[:20]
        ctx['target_user'] = self.request.user
        return ctx


class UserDetailView(CanAddDaroodMixin, TemplateView):
    """Per-user darood breakdown for managers / superadmins."""

    template_name = 'darood/user_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = get_object_or_404(User, pk=kwargs['pk'])
        period = _current_period(self.request)
        entries = filter_by_period(DaroodEntry.objects.filter(user=target), period)
        ctx['target_user'] = target
        ctx['period'] = period
        ctx['periods'] = PERIODS
        ctx['total'] = total_count(entries)
        ctx['entry_count'] = entries.count()
        ctx['recent'] = entries.select_related('recorded_by')[:30]
        return ctx


class ChartDataAPI(LoginRequiredMixin, TemplateView):
    """Time-series JSON for Chart.js.

    Query params:
      * ``granularity`` = day | month | year   (default: day)
      * ``user``        = user id               (optional)
      * ``scope``       = all | mine            (default depends on role)

    Access rules: a simple user may only request their own data.
    """

    def get(self, request, *args, **kwargs):
        granularity = request.GET.get('granularity', 'day')
        if granularity not in {'day', 'month', 'year'}:
            granularity = 'day'

        qs = DaroodEntry.objects.all()

        user_id = request.GET.get('user')
        scope = request.GET.get('scope')

        if user_id:
            qs = qs.filter(user_id=user_id)
        elif scope == 'mine' or not request.user.can_add_darood:
            # Simple users are always scoped to themselves.
            qs = qs.filter(user=request.user)

        # Guard: a non-privileged user cannot read someone else's series.
        if not request.user.can_add_darood and user_id and str(user_id) != str(request.user.pk):
            qs = DaroodEntry.objects.filter(user=request.user)

        series = time_series(qs, granularity)
        return JsonResponse(
            {
                'granularity': granularity,
                'labels': [row['label'] for row in series],
                'totals': [row['total'] for row in series],
            }
        )
