"""Query helpers for filtering and aggregating darood entries."""

from datetime import date, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek, TruncYear
from django.utils.translation import gettext_lazy as _

# Supported reporting periods (label shown in the UI -> key used in querystrings).
PERIODS = [
    ('day', _('Today')),
    ('week', _('This Week')),
    ('month', _('This Month')),
    ('year', _('This Year')),
    ('all', _('All Time')),
]
VALID_PERIODS = {key for key, _ in PERIODS}

# Granularity for the time-series charts.
GRANULARITIES = {
    'day': TruncDay,
    'week': TruncWeek,
    'month': TruncMonth,
    'year': TruncYear,
}


def period_range(period, today=None):
    """Return an inclusive ``(start, end)`` date pair for a period.

    ``None`` for either bound means "unbounded". ``today`` defaults to the
    real current date but can be injected for testing.
    """
    today = today or date.today()

    if period == 'day':
        return today, today
    if period == 'week':
        # ISO week: Monday .. Sunday containing today.
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if period == 'month':
        start = today.replace(day=1)
        # First day of next month minus one day.
        next_month = (start + timedelta(days=32)).replace(day=1)
        return start, next_month - timedelta(days=1)
    if period == 'year':
        return today.replace(month=1, day=1), today.replace(month=12, day=31)
    # 'all' or anything unknown -> unbounded.
    return None, None


def filter_by_period(queryset, period, today=None):
    """Restrict a ``DaroodEntry`` queryset to the given period."""
    if period not in VALID_PERIODS:
        period = 'month'
    start, end = period_range(period, today=today)
    if start is not None:
        queryset = queryset.filter(date__gte=start)
    if end is not None:
        queryset = queryset.filter(date__lte=end)
    return queryset


def total_count(queryset):
    return queryset.aggregate(total=Sum('count'))['total'] or 0


def reserve_summary(user):
    """Totals for a manager's private darood reserve.

    Returns a dict with the amount ever ``added``, the amount ever ``submitted``
    (released into the public record) and the current ``balance`` still held in
    reserve. Balance never goes negative because submissions are validated
    against it before being recorded.
    """
    from django.db.models import Q

    from .models import ReserveTransaction

    agg = ReserveTransaction.objects.filter(manager=user).aggregate(
        added=Sum('count', filter=Q(kind=ReserveTransaction.Kind.ADD)),
        submitted=Sum('count', filter=Q(kind=ReserveTransaction.Kind.SUBMIT)),
    )
    added = agg['added'] or 0
    submitted = agg['submitted'] or 0
    return {'added': added, 'submitted': submitted, 'balance': added - submitted}


LABEL_FMT = {
    'day': '%d %b',
    'week': 'w/c %d %b',   # week commencing (Monday)
    'month': '%b %Y',
    'year': '%Y',
}


def _bucket_start(d, granularity):
    """Snap a date to the start of its bucket (matches Trunc* behaviour)."""
    if granularity == 'week':
        return d - timedelta(days=d.weekday())      # Monday
    if granularity == 'month':
        return d.replace(day=1)
    if granularity == 'year':
        return d.replace(month=1, day=1)
    return d


def _next_bucket(d, granularity):
    if granularity == 'week':
        return d + timedelta(days=7)
    if granularity == 'month':
        return (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    if granularity == 'year':
        return d.replace(year=d.year + 1, month=1, day=1)
    return d + timedelta(days=1)


def _totals_by_bucket(queryset, granularity):
    trunc = GRANULARITIES.get(granularity, TruncDay)
    totals = {}
    rows = (
        queryset.annotate(bucket=trunc('date'))
        .values('bucket')
        .annotate(total=Sum('count'))
    )
    for row in rows:
        bucket = row['bucket']
        if bucket is None:
            continue
        if hasattr(bucket, 'date'):   # datetime -> date
            bucket = bucket.date()
        totals[bucket] = row['total'] or 0
    return totals


def time_series(queryset, granularity='day'):
    """Sparse series: only buckets that actually have data (used for all-time)."""
    fmt = LABEL_FMT.get(granularity, '%d %b')
    totals = _totals_by_bucket(queryset, granularity)
    return [
        {'label': b.strftime(fmt), 'total': totals[b]}
        for b in sorted(totals)
    ]


def bucket_starts(granularity, start, end):
    """List of bucket start-dates spanning [start, end] at the granularity."""
    out = []
    cur = _bucket_start(start, granularity)
    last = _bucket_start(end, granularity)
    guard = 0
    while cur <= last and guard < 4000:
        out.append(cur)
        cur = _next_bucket(cur, granularity)
        guard += 1
    return out


def filled_time_series(queryset, granularity, start, end):
    """Continuous series across [start, end]: every bucket present, 0 if empty.

    This is what charts should use for a bounded window so a day with no
    darood shows as 0 instead of the line jumping straight to the next day.
    """
    fmt = LABEL_FMT.get(granularity, '%d %b')
    totals = _totals_by_bucket(queryset, granularity)

    result = []
    cur = _bucket_start(start, granularity)
    last = _bucket_start(end, granularity)
    guard = 0
    while cur <= last and guard < 4000:
        result.append({'label': cur.strftime(fmt), 'total': totals.get(cur, 0)})
        cur = _next_bucket(cur, granularity)
        guard += 1
    return result
