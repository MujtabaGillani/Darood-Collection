from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, TemplateView, View

from accounts.permissions import CanAddDaroodMixin
from .forms import (
    AddDaroodForm,
    AddReserveForm,
    SubmitDaroodForm,
    UseReserveForm,
    addable_users_queryset,
)
from .models import DaroodEntry, ReserveTransaction
from .services import (
    PERIODS,
    filled_time_series,
    filter_by_period,
    reserve_summary,
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


def _reserve_context(user, reserve_add_form=None, reserve_use_form=None):
    """Shared context for the reserve panel on the Record Darood page."""
    summary = reserve_summary(user)
    today = timezone.localdate()
    return {
        'reserve': summary,
        'reserve_history': (
            ReserveTransaction.objects.filter(manager=user).select_related('entry')[:20]
        ),
        'reserve_add_form': (
            reserve_add_form if reserve_add_form is not None
            else AddReserveForm(initial={'date': today})
        ),
        'reserve_use_form': (
            reserve_use_form if reserve_use_form is not None
            else UseReserveForm(balance=summary['balance'], initial={'date': today})
        ),
    }


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
            _('Recorded %(count)s darood for %(name)s on %(date)s.') % {
                'count': entry.count, 'name': entry.user.full_name,
                'date': f'{entry.date:%d %b %Y}'},
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent'] = (
            DaroodEntry.objects.select_related('user')
            .filter(recorded_by=self.request.user)[:10]
        )
        # Which tab / sub-tab the reserve panel should open on (set after a
        # reserve action redirects back here).
        ctx['active_tab'] = 'reserve' if self.request.GET.get('tab') == 'reserve' else 'record'
        ctx['reserve_sub'] = 'use' if self.request.GET.get('sub') == 'use' else 'add'
        ctx.update(_reserve_context(self.request.user))
        return ctx


# ---------------------------------------------------------------------------
# Reserve (a manager's private darood stash)
# ---------------------------------------------------------------------------
class AddReserveView(CanAddDaroodMixin, View):
    """A manager adds darood to their own private reserve (not yet public)."""

    def post(self, request):
        form = AddReserveForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.manager = request.user
            txn.kind = ReserveTransaction.Kind.ADD
            txn.save()
            messages.success(
                request,
                _('Added %(count)s darood to your reserve for %(date)s.') % {
                    'count': txn.count, 'date': f'{txn.date:%d %b %Y}'},
            )
            return redirect(reverse('add_darood') + '?tab=reserve&sub=add')

        for field_errors in form.errors.values():
            for err in field_errors:
                messages.error(request, err)
        return redirect(reverse('add_darood') + '?tab=reserve&sub=add')


class UseReserveView(CanAddDaroodMixin, View):
    """A manager submits part of their reserve, publishing it as approved darood."""

    def post(self, request):
        summary = reserve_summary(request.user)
        form = UseReserveForm(request.POST, balance=summary['balance'])
        if form.is_valid():
            count = form.cleaned_data['count']
            entry_date = form.cleaned_data['date']
            with transaction.atomic():
                entry = DaroodEntry.objects.create(
                    user=request.user,
                    manager=request.user,
                    recorded_by=request.user,
                    count=count,
                    date=entry_date,
                    status=DaroodEntry.Status.APPROVED,
                    reviewed_at=timezone.now(),
                )
                ReserveTransaction.objects.create(
                    manager=request.user,
                    kind=ReserveTransaction.Kind.SUBMIT,
                    count=count,
                    date=entry_date,
                    entry=entry,
                )
            messages.success(
                request,
                _('Submitted %(count)s darood from your reserve for %(date)s. '
                  'It now counts toward the total.') % {
                    'count': count, 'date': f'{entry_date:%d %b %Y}'},
            )
            return redirect(reverse('add_darood') + '?tab=reserve&sub=use')

        for field_errors in form.errors.values():
            for err in field_errors:
                messages.error(request, err)
        return redirect(reverse('add_darood') + '?tab=reserve&sub=use')


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
            _('Submitted %(count)s darood for %(date)s to %(manager)s. '
              'It will count once approved.') % {
                'count': entry.count, 'date': f'{entry.date:%d %b %Y}',
                'manager': entry.manager.full_name},
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
            messages.error(request, _('You cannot review this submission.'))
            return redirect('approvals')

        if not entry.is_pending:
            messages.info(request, _('This submission has already been reviewed.'))
            return redirect('approvals')

        decision = request.POST.get('decision')
        if decision == 'approve':
            entry.status = DaroodEntry.Status.APPROVED
        elif decision == 'reject':
            entry.status = DaroodEntry.Status.REJECTED
        else:
            messages.error(request, _('Invalid decision.'))
            return redirect('approvals')

        entry.reviewed_at = timezone.now()
        entry.save(update_fields=['status', 'reviewed_at'])
        ctx = {'name': entry.user.full_name, 'count': entry.count, 'date': f'{entry.date:%d %b %Y}'}
        if decision == 'approve':
            messages.success(request, _("Approved %(name)s's %(count)s darood (%(date)s).") % ctx)
        else:
            messages.success(request, _("Rejected %(name)s's %(count)s darood (%(date)s).") % ctx)
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


class FazailView(LoginRequiredMixin, TemplateView):
    """Static devotional page: verified hadiths on the virtue of Darood."""

    template_name = 'darood/fazail.html'


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


def _display_name(row, prefix):
    first = (row.get(prefix + 'first_name') or '').strip()
    last = (row.get(prefix + 'last_name') or '').strip()
    full = f'{first} {last}'.strip()
    return full or row.get(prefix + 'username')


def _window_start(request):
    """(start, end) for a ?days=N window, or (earliest entry, today) for all-time."""
    from datetime import timedelta

    today = timezone.localdate()
    days = request.GET.get('days')
    if days and days.isdigit() and int(days) > 0:
        return today - timedelta(days=int(days) - 1), today
    first = approved_entries().order_by('date').values_list('date', flat=True).first()
    return (first or today), today


def _id_list(request, key):
    """Parse ``?key=1,2,3`` into a list of ints, ignoring junk."""
    raw = request.GET.get(key, '')
    return [int(x) for x in raw.split(',') if x.strip().isdigit()]


def _multi_series(qs, group_field, prefix, granularity, start, end):
    """Build a Chart.js multi-line payload: one dataset per group value.

    ``group_field`` is the id column to group on (e.g. ``'manager'``) and
    ``prefix`` the related-name prefix for its display fields
    (e.g. ``'manager__'``). Datasets are ordered by total, descending.
    """
    from django.db.models import Sum
    from .services import GRANULARITIES, LABEL_FMT, bucket_starts

    trunc = GRANULARITIES[granularity]
    rows = (
        qs.filter(date__gte=start, date__lte=end)
        .annotate(bucket=trunc('date'))
        .values(group_field, prefix + 'first_name', prefix + 'last_name',
                prefix + 'username', 'bucket')
        .annotate(total=Sum('count'))
    )

    buckets = bucket_starts(granularity, start, end)
    fmt = LABEL_FMT.get(granularity, '%d %b')

    groups = {}
    for row in rows:
        gid = row[group_field]
        if gid not in groups:
            groups[gid] = {'label': _display_name(row, prefix), 'data': {}}
        bucket = row['bucket']
        if hasattr(bucket, 'date'):
            bucket = bucket.date()
        groups[gid]['data'][bucket] = row['total'] or 0

    datasets = [
        {'label': g['label'], 'data': [g['data'].get(b, 0) for b in buckets]}
        for g in sorted(groups.values(), key=lambda g: sum(g['data'].values()), reverse=True)
    ]
    return {
        'labels': [b.strftime(fmt) for b in buckets],
        'datasets': datasets,
        'start': start.isoformat(),
        'end': end.isoformat(),
    }


class ManagerSeriesAPI(CanAddDaroodMixin, View):
    """Multi-line data: one series per manager = darood they collected.

    Optional ``?managers=1,2`` narrows to specific managers; omit for all.
    """

    def get(self, request, *args, **kwargs):
        from .services import GRANULARITIES

        granularity = request.GET.get('granularity', 'day')
        if granularity not in GRANULARITIES:
            granularity = 'day'
        start, end = _window_start(request)

        qs = approved_entries().filter(manager__isnull=False)
        ids = _id_list(request, 'managers')
        if ids:
            qs = qs.filter(manager_id__in=ids)

        payload = _multi_series(qs, 'manager', 'manager__', granularity, start, end)
        return JsonResponse(payload)


class UserSeriesAPI(CanAddDaroodMixin, View):
    """Multi-line data: one series per reciter = darood they recited.

    Optional ``?users=1,2`` narrows to specific users; omit for all.
    """

    def get(self, request, *args, **kwargs):
        from .services import GRANULARITIES

        granularity = request.GET.get('granularity', 'day')
        if granularity not in GRANULARITIES:
            granularity = 'day'
        start, end = _window_start(request)

        qs = approved_entries()
        ids = _id_list(request, 'users')
        if ids:
            qs = qs.filter(user_id__in=ids)

        payload = _multi_series(qs, 'user', 'user__', granularity, start, end)
        return JsonResponse(payload)


class TopStatsAPI(CanAddDaroodMixin, View):
    """Top collector (manager) and top reciter (user) within the window."""

    def get(self, request, *args, **kwargs):
        from django.db.models import Sum

        start, end = _window_start(request)
        qs = approved_entries().filter(date__gte=start, date__lte=end)

        top_user_row = (
            qs.values('user__first_name', 'user__last_name', 'user__username')
            .annotate(t=Sum('count')).order_by('-t').first()
        )
        top_mgr_row = (
            qs.filter(manager__isnull=False)
            .values('manager__first_name', 'manager__last_name', 'manager__username')
            .annotate(t=Sum('count')).order_by('-t').first()
        )
        return JsonResponse({
            'top_user': {'name': _display_name(top_user_row, 'user__'), 'total': top_user_row['t']}
                        if top_user_row else None,
            'top_manager': {'name': _display_name(top_mgr_row, 'manager__'), 'total': top_mgr_row['t']}
                           if top_mgr_row else None,
        })
