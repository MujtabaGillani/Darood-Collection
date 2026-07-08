from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, View

from accounts.permissions import CanAddDaroodMixin
from .forms import AddDaroodForm, SubmitDaroodForm, addable_users_queryset
from .models import DaroodEntry
from .services import (
    PERIODS,
    filled_time_series,
    filter_by_period,
    time_series,
    total_count,
)

User = get_user_model()


def approved_entries():
    """Base queryset of entries that actually count toward totals."""
    return DaroodEntry.objects.filter(status=DaroodEntry.Status.APPROVED)


def _current_period(request):
    period = request.GET.get('period', 'month')
    return period if period in {k for k, _ in PERIODS} else 'month'


# ---------------------------------------------------------------------------
# Recording darood
# ---------------------------------------------------------------------------
class AddDaroodView(CanAddDaroodMixin, CreateView):
    """Managers / superadmins record a darood count for a searched user.

    Entered by a trusted user, so it is APPROVED immediately.
    """

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
        entry = form.instance
        entry.recorded_by = self.request.user
        entry.manager = self.request.user
        entry.status = DaroodEntry.Status.APPROVED
        entry.reviewed_at = timezone.now()
        response = super().form_valid(form)
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


class SubmitDaroodView(LoginRequiredMixin, CreateView):
    """A simple user submits their own darood to a manager for approval."""

    model = DaroodEntry
    form_class = SubmitDaroodForm
    template_name = 'darood/submit.html'
    success_url = reverse_lazy('my_progress')

    def get_initial(self):
        return {'date': timezone.localdate()}

    def form_valid(self, form):
        entry = form.instance
        entry.user = self.request.user          # a user submits for themselves
        entry.recorded_by = self.request.user
        entry.status = DaroodEntry.Status.PENDING
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Submitted {entry.count} darood for {entry.date:%d %b %Y} to '
            f'{entry.manager.full_name}. It will count once approved.',
        )
        return response


# ---------------------------------------------------------------------------
# Approval queue (managers / superadmins)
# ---------------------------------------------------------------------------
class ApprovalsView(CanAddDaroodMixin, TemplateView):
    """Pending submissions awaiting review.

    A manager sees submissions addressed to them; a superadmin sees all.
    """

    template_name = 'darood/approvals.html'

    def pending_qs(self):
        qs = DaroodEntry.objects.filter(
            status=DaroodEntry.Status.PENDING
        ).select_related('user', 'manager')
        if not self.request.user.is_superadmin:
            qs = qs.filter(manager=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pending'] = self.pending_qs()
        ctx['reviewed'] = (
            DaroodEntry.objects.exclude(status=DaroodEntry.Status.PENDING)
            .filter(reviewed_at__isnull=False, manager=self.request.user)
            .select_related('user')[:15]
        )
        return ctx


class ReviewEntryView(CanAddDaroodMixin, View):
    """Accept or reject a pending submission."""

    def post(self, request, pk):
        entry = get_object_or_404(DaroodEntry, pk=pk)

        # Only the assigned manager (or a superadmin) may act on it.
        if not request.user.is_superadmin and entry.manager_id != request.user.pk:
            messages.error(request, 'You cannot review this submission.')
            return redirect('approvals')

        if not entry.is_pending:
            messages.info(request, 'This submission has already been reviewed.')
            return redirect('approvals')

        decision = request.POST.get('decision')
        if decision == 'approve':
            entry.status = DaroodEntry.Status.APPROVED
        elif decision == 'reject':
            entry.status = DaroodEntry.Status.REJECTED
        else:
            messages.error(request, 'Invalid decision.')
            return redirect('approvals')

        entry.reviewed_at = timezone.now()
        entry.save(update_fields=['status', 'reviewed_at'])
        verb = 'approved' if decision == 'approve' else 'rejected'
        messages.success(
            request,
            f"{entry.user.full_name}'s {entry.count} darood ({entry.date:%d %b %Y}) {verb}.",
        )
        return redirect('approvals')


# ---------------------------------------------------------------------------
# Viewing
# ---------------------------------------------------------------------------
class DaroodOverviewView(LoginRequiredMixin, TemplateView):
    """Aggregate view of ALL users' approved darood (managers/superadmin)."""

    template_name = 'darood/overview.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.can_add_darood:
            return redirect('my_progress')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.db.models import Sum

        ctx = super().get_context_data(**kwargs)
        period = _current_period(self.request)
        entries = filter_by_period(approved_entries(), period)

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
    """A user's own darood progress with a period filter + chart.

    Totals/chart count APPROVED entries; the recent list shows every status so
    the user can see what is still pending or was rejected.
    """

    template_name = 'darood/my_progress.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = _current_period(self.request)
        mine = DaroodEntry.objects.filter(user=self.request.user)
        approved = filter_by_period(mine.filter(status=DaroodEntry.Status.APPROVED), period)

        ctx['period'] = period
        ctx['periods'] = PERIODS
        ctx['total'] = total_count(approved)
        ctx['entry_count'] = approved.count()
        ctx['pending_count'] = mine.filter(status=DaroodEntry.Status.PENDING).count()
        ctx['recent'] = mine.select_related('manager', 'recorded_by')[:20]
        ctx['target_user'] = self.request.user
        return ctx


class UserDetailView(CanAddDaroodMixin, TemplateView):
    """Per-user approved darood breakdown for managers / superadmins."""

    template_name = 'darood/user_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = get_object_or_404(User, pk=kwargs['pk'])
        period = _current_period(self.request)
        entries = filter_by_period(
            approved_entries().filter(user=target), period
        )
        ctx['target_user'] = target
        ctx['period'] = period
        ctx['periods'] = PERIODS
        ctx['total'] = total_count(entries)
        ctx['entry_count'] = entries.count()
        ctx['recent'] = entries.select_related('recorded_by')[:30]
        return ctx


# ---------------------------------------------------------------------------
# JSON APIs
# ---------------------------------------------------------------------------
class UserSearchAPI(CanAddDaroodMixin, View):
    """JSON autocomplete for the add-darood search box (role-scoped)."""

    def get(self, request, *args, **kwargs):
        from django.db.models import Q

        q = request.GET.get('q', '').strip()
        qs = addable_users_queryset(request.user)
        if q:
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


class ChartDataAPI(LoginRequiredMixin, View):
    """Time-series JSON of APPROVED darood for Chart.js.

    Query params:
      * ``granularity`` = day | week | month | year   (default: day)
      * ``days``        = lookback window in days      (optional; omit = all)
      * ``user``        = user id                      (optional)
      * ``scope``       = all | mine

    A simple user may only ever read their own series.
    """

    def get(self, request, *args, **kwargs):
        from datetime import timedelta

        granularity = request.GET.get('granularity', 'day')
        if granularity not in {'day', 'week', 'month', 'year'}:
            granularity = 'day'

        qs = approved_entries()

        user_id = request.GET.get('user')
        scope = request.GET.get('scope')

        if user_id:
            qs = qs.filter(user_id=user_id)
        elif scope == 'mine' or not request.user.can_add_darood:
            qs = qs.filter(user=request.user)

        # Guard: a non-privileged user cannot read someone else's series.
        if not request.user.can_add_darood and user_id and str(user_id) != str(request.user.pk):
            qs = approved_entries().filter(user=request.user)

        days = request.GET.get('days')
        if days and days.isdigit() and int(days) > 0:
            # Bounded window -> continuous, zero-filled series so empty days
            # render as 0 rather than being interpolated over.
            today = timezone.localdate()
            start = today - timedelta(days=int(days) - 1)
            qs = qs.filter(date__gte=start, date__lte=today)
            series = filled_time_series(qs, granularity, start, today)
        else:
            # All-time (e.g. By Years): sparse is fine.
            series = time_series(qs, granularity)
        return JsonResponse(
            {
                'granularity': granularity,
                'labels': [row['label'] for row in series],
                'totals': [row['total'] for row in series],
            }
        )
