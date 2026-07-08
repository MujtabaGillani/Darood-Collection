"""Mobile/JSON API views (JWT-authenticated).

Purely additive — none of the existing web views or templates are touched.
Business rules mirror the server-rendered views so both clients agree.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from darood.forms import addable_users_queryset, managers_queryset
from darood.models import DaroodEntry
from darood.services import (
    GRANULARITIES,
    PERIODS,
    filled_time_series,
    filter_by_period,
    time_series,
    total_count,
)
from darood.views import _multi_series, approved_entries

from .permissions import CanAddDarood, IsSuperadmin
from .serializers import (
    ChangePasswordSerializer,
    DaroodEntrySerializer,
    LoginSerializer,
    QuickAddUserSerializer,
    RecordDaroodSerializer,
    RegisterSerializer,
    SubmitDaroodSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Small helpers (query-param parsing for charts)
# ---------------------------------------------------------------------------
def _granularity(params):
    g = params.get('granularity', 'day')
    return g if g in GRANULARITIES else 'day'


def _window(params):
    """(start, end) for a ?days=N window, or (earliest entry, today) otherwise."""
    today = timezone.localdate()
    days = params.get('days')
    if days and days.isdigit() and int(days) > 0:
        return today - timedelta(days=int(days) - 1), today
    first = approved_entries().order_by('date').values_list('date', flat=True).first()
    return (first or today), today


def _ids(params, key):
    raw = params.get(key, '')
    return [int(x) for x in raw.split(',') if x.strip().isdigit()]


def _periods_payload():
    return [{'key': key, 'label': str(label)} for key, label in PERIODS]


def _current_period(params):
    period = params.get('period', 'month')
    return period if period in {k for k, _ in PERIODS} else 'month'


def _my_total(user):
    return approved_entries().filter(user=user).aggregate(t=Sum('count'))['t'] or 0


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Registration successful. Your account is pending approval '
                       'by an administrator.'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class LogoutView(APIView):
    """Invalidate the given refresh token so it can't be reused after logout."""

    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass  # already expired/invalid — nothing to do
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    def get(self, request):
        user = request.user
        user.darood_total = _my_total(user)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    """Any logged-in user changes their own password (current + new x2)."""

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password changed successfully.'})


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserListView(generics.ListAPIView):
    """Super admin: all users with their approved totals (dashboard table)."""

    serializer_class = UserSerializer
    permission_classes = [IsSuperadmin]

    def get_queryset(self):
        qs = User.objects.annotate(
            darood_total=Sum(
                'darood_entries__count',
                filter=Q(darood_entries__status=DaroodEntry.Status.APPROVED),
            )
        ).order_by('-date_joined')
        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class UserSearchView(APIView):
    """Manager / super admin: role-scoped autocomplete for the add-darood flow."""

    permission_classes = [CanAddDarood]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        qs = addable_users_queryset(request.user)
        if q:
            qs = qs.filter(
                Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        return Response(UserSerializer(qs[:15], many=True).data)


class ManagerListView(APIView):
    """Active managers a simple user can submit their darood to."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(managers_queryset(), many=True).data)


class QuickAddUserView(generics.CreateAPIView):
    serializer_class = QuickAddUserSerializer
    permission_classes = [CanAddDarood]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        from accounts.forms import QUICK_ADD_DEFAULT_PASSWORD
        return Response(
            {'user': UserSerializer(user).data, 'default_password': QUICK_ADD_DEFAULT_PASSWORD},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(APIView):
    """Manager / super admin: a single user's approved breakdown for a period."""

    permission_classes = [CanAddDarood]

    def get(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        period = _current_period(request.query_params)
        entries = filter_by_period(approved_entries().filter(user=target), period)
        recent = entries.select_related('recorded_by')[:30]
        return Response({
            'user': UserSerializer(target).data,
            'period': period,
            'periods': _periods_payload(),
            'total': total_count(entries),
            'entry_count': entries.count(),
            'recent': DaroodEntrySerializer(recent, many=True).data,
        })


class UserUpdateView(APIView):
    """Super admin: change role / active status (mirrors the dashboard form)."""

    permission_classes = [IsSuperadmin]

    def patch(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        if target.is_superadmin:
            return Response(
                {'detail': 'Super Admin accounts cannot be modified here.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserUpdateSerializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'role' in data:
            target.role = data['role']
            # A manager also needs Django staff access; a simple user does not.
            target.is_staff = data['role'] == User.Role.MANAGER
            target.is_superuser = False
        if 'is_active' in data:
            target.is_active = data['is_active']
        target.save()
        return Response(UserSerializer(target).data)


# ---------------------------------------------------------------------------
# Recording / submitting darood
# ---------------------------------------------------------------------------
class RecordDaroodView(APIView):
    permission_classes = [CanAddDarood]

    def post(self, request):
        serializer = RecordDaroodSerializer(data=request.data, request_user=request.user)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save(
            recorded_by=request.user,
            manager=request.user,
            status=DaroodEntry.Status.APPROVED,
            reviewed_at=timezone.now(),
        )
        return Response(DaroodEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class SubmitDaroodView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitDaroodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save(
            user=request.user,
            recorded_by=request.user,
            status=DaroodEntry.Status.PENDING,
        )
        return Response(DaroodEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class MyProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = _current_period(request.query_params)
        mine = DaroodEntry.objects.filter(user=request.user)
        approved = filter_by_period(mine.filter(status=DaroodEntry.Status.APPROVED), period)
        recent = mine.select_related('manager', 'recorded_by')[:20]
        return Response({
            'period': period,
            'periods': _periods_payload(),
            'total': total_count(approved),
            'entry_count': approved.count(),
            'pending_count': mine.filter(status=DaroodEntry.Status.PENDING).count(),
            'recent': DaroodEntrySerializer(recent, many=True).data,
        })


class OverviewView(APIView):
    permission_classes = [CanAddDarood]

    def get(self, request):
        period = _current_period(request.query_params)
        entries = filter_by_period(approved_entries(), period)
        leaderboard = (
            entries.values('user_id', 'user__username', 'user__first_name', 'user__last_name')
            .annotate(total=Sum('count'))
            .order_by('-total')[:10]
        )
        board = [
            {
                'user_id': row['user_id'],
                'name': (f"{row['user__first_name']} {row['user__last_name']}".strip()
                         or row['user__username']),
                'total': row['total'],
            }
            for row in leaderboard
        ]
        recent = entries.select_related('user', 'recorded_by')[:20]
        return Response({
            'period': period,
            'periods': _periods_payload(),
            'total': total_count(entries),
            'entry_count': entries.count(),
            'contributor_count': entries.values('user').distinct().count(),
            'leaderboard': board,
            'recent': DaroodEntrySerializer(recent, many=True).data,
        })


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------
class ApprovalsView(APIView):
    permission_classes = [CanAddDarood]

    def get(self, request):
        pending = DaroodEntry.objects.filter(
            status=DaroodEntry.Status.PENDING
        ).select_related('user', 'manager')
        if not request.user.is_superadmin:
            pending = pending.filter(manager=request.user)
        reviewed = (
            DaroodEntry.objects.exclude(status=DaroodEntry.Status.PENDING)
            .filter(reviewed_at__isnull=False, manager=request.user)
            .select_related('user')[:15]
        )
        return Response({
            'pending': DaroodEntrySerializer(pending, many=True).data,
            'reviewed': DaroodEntrySerializer(reviewed, many=True).data,
        })


class ReviewEntryView(APIView):
    permission_classes = [CanAddDarood]

    def post(self, request, pk):
        entry = get_object_or_404(DaroodEntry, pk=pk)
        if not request.user.is_superadmin and entry.manager_id != request.user.pk:
            return Response({'detail': 'You cannot review this submission.'},
                            status=status.HTTP_403_FORBIDDEN)
        if not entry.is_pending:
            return Response({'detail': 'This submission has already been reviewed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        decision = request.data.get('decision')
        if decision == 'approve':
            entry.status = DaroodEntry.Status.APPROVED
        elif decision == 'reject':
            entry.status = DaroodEntry.Status.REJECTED
        else:
            return Response({'detail': 'Invalid decision.'}, status=status.HTTP_400_BAD_REQUEST)

        entry.reviewed_at = timezone.now()
        entry.save(update_fields=['status', 'reviewed_at'])
        return Response(DaroodEntrySerializer(entry).data)


# ---------------------------------------------------------------------------
# Charts & stats
# ---------------------------------------------------------------------------
class TrendChartView(APIView):
    """Single time-series of approved darood (self, all, or a specific user)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        granularity = _granularity(params)
        qs = approved_entries()

        user_id = params.get('user')
        scope = params.get('scope')
        if user_id:
            qs = qs.filter(user_id=user_id)
        elif scope == 'mine' or not request.user.can_add_darood:
            qs = qs.filter(user=request.user)
        # Guard: a non-privileged user cannot read someone else's series.
        if not request.user.can_add_darood and user_id and str(user_id) != str(request.user.pk):
            qs = approved_entries().filter(user=request.user)

        days = params.get('days')
        if days and days.isdigit() and int(days) > 0:
            today = timezone.localdate()
            start = today - timedelta(days=int(days) - 1)
            qs = qs.filter(date__gte=start, date__lte=today)
            series = filled_time_series(qs, granularity, start, today)
        else:
            series = time_series(qs, granularity)
        return Response({
            'granularity': granularity,
            'labels': [r['label'] for r in series],
            'totals': [r['total'] for r in series],
        })


class ManagerSeriesView(APIView):
    permission_classes = [CanAddDarood]

    def get(self, request):
        params = request.query_params
        granularity = _granularity(params)
        start, end = _window(params)
        qs = approved_entries().filter(manager__isnull=False)
        ids = _ids(params, 'managers')
        if ids:
            qs = qs.filter(manager_id__in=ids)
        return Response(_multi_series(qs, 'manager', 'manager__', granularity, start, end))


class UserSeriesView(APIView):
    permission_classes = [CanAddDarood]

    def get(self, request):
        params = request.query_params
        granularity = _granularity(params)
        start, end = _window(params)
        qs = approved_entries()
        ids = _ids(params, 'users')
        if ids:
            qs = qs.filter(user_id__in=ids)
        return Response(_multi_series(qs, 'user', 'user__', granularity, start, end))


class TopStatsView(APIView):
    permission_classes = [CanAddDarood]

    def get(self, request):
        start, end = _window(request.query_params)
        qs = approved_entries().filter(date__gte=start, date__lte=end)

        def name(row, prefix):
            first = (row.get(prefix + 'first_name') or '').strip()
            last = (row.get(prefix + 'last_name') or '').strip()
            return f'{first} {last}'.strip() or row.get(prefix + 'username')

        top_user = (
            qs.values('user__first_name', 'user__last_name', 'user__username')
            .annotate(t=Sum('count')).order_by('-t').first()
        )
        top_mgr = (
            qs.filter(manager__isnull=False)
            .values('manager__first_name', 'manager__last_name', 'manager__username')
            .annotate(t=Sum('count')).order_by('-t').first()
        )
        return Response({
            'top_user': {'name': name(top_user, 'user__'), 'total': top_user['t']} if top_user else None,
            'top_manager': {'name': name(top_mgr, 'manager__'), 'total': top_mgr['t']} if top_mgr else None,
        })


class DashboardStatsView(APIView):
    """Super admin dashboard summary: tiles + the chart filter option lists."""

    permission_classes = [IsSuperadmin]

    def get(self, request):
        users = User.objects.all()
        name_order = ('first_name', 'last_name', 'username')
        managers = User.objects.filter(
            Q(role=User.Role.MANAGER) | Q(role=User.Role.SUPERADMIN) | Q(is_superuser=True)
        ).distinct().order_by(*name_order)
        simple_users = User.objects.filter(role=User.Role.SIMPLE).order_by(*name_order)
        grand_total = approved_entries().aggregate(t=Sum('count'))['t'] or 0
        return Response({
            'grand_total': grand_total,
            'total_users': users.count(),
            'active_count': users.filter(is_active=True).count(),
            'pending_count': users.filter(is_active=False).count(),
            'managers': [{'id': u.pk, 'name': u.full_name} for u in managers],
            'users': [{'id': u.pk, 'name': u.full_name} for u in simple_users],
        })
