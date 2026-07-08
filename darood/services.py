"""Query helpers for filtering and aggregating darood entries."""

from datetime import date, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear

# Supported reporting periods (label shown in the UI -> key used in querystrings).
PERIODS = [
    ('day', 'Today'),
    ('week', 'This Week'),
    ('month', 'This Month'),
    ('year', 'This Year'),
    ('all', 'All Time'),
]
VALID_PERIODS = {key for key, _ in PERIODS}

# Granularity for the time-series charts.
GRANULARITIES = {
    'day': TruncDay,
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


def time_series(queryset, granularity='day'):
    """Aggregate a queryset into ``[{'label': ..., 'total': ...}, ...]``.

    Grouped and ordered chronologically by day / month / year.
    """
    trunc = GRANULARITIES.get(granularity, TruncDay)
    fmt = {
        'day': '%Y-%m-%d',
        'month': '%b %Y',
        'year': '%Y',
    }.get(granularity, '%Y-%m-%d')

    rows = (
        queryset.annotate(bucket=trunc('date'))
        .values('bucket')
        .annotate(total=Sum('count'))
        .order_by('bucket')
    )
    return [
        {'label': row['bucket'].strftime(fmt), 'total': row['total'] or 0}
        for row in rows
        if row['bucket'] is not None
    ]
