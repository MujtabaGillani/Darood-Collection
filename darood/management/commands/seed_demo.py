"""Seed the database with demo users and darood entries for local testing.

Usage:  python manage.py seed_demo
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from darood.models import DaroodEntry

User = get_user_model()

DEMO_USERS = [
    # username, first, last, role, active
    ('admin', 'Super', 'Admin', User.Role.SUPERADMIN, True),
    ('manager1', 'Bilal', 'Ahmed', User.Role.MANAGER, True),
    ('manager2', 'Fatima', 'Khan', User.Role.MANAGER, True),
    ('user1', 'Usman', 'Ali', User.Role.SIMPLE, True),
    ('user2', 'Ayesha', 'Malik', User.Role.SIMPLE, True),
    ('user3', 'Hamza', 'Sheikh', User.Role.SIMPLE, True),
    ('pending1', 'Zainab', 'Iqbal', User.Role.SIMPLE, False),  # awaiting approval
]

PASSWORD = 'darood123'


class Command(BaseCommand):
    help = 'Create demo users and darood entries.'

    def handle(self, *args, **options):
        created_users = {}
        for username, first, last, role, active in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last},
            )
            user.first_name = first
            user.last_name = last
            user.role = role
            user.is_active = active
            user.is_superuser = role == User.Role.SUPERADMIN
            user.is_staff = role in (User.Role.SUPERADMIN, User.Role.MANAGER)
            user.set_password(PASSWORD)
            user.save()
            created_users[username] = user
            self.stdout.write(f'  {"created" if created else "updated"}: {username} ({role})')

        # Approved history spread over the last ~40 days for the simple users.
        manager = created_users['manager1']
        now = timezone.now()
        today = timezone.localdate()
        DaroodEntry.objects.all().delete()
        counts = {'user1': [100, 250, 300], 'user2': [500, 120], 'user3': [80, 400, 200, 150]}
        entries = 0
        for i in range(40):
            day = today - timedelta(days=i)
            for uname, amounts in counts.items():
                amount = amounts[i % len(amounts)]
                DaroodEntry.objects.create(
                    user=created_users[uname], count=amount, date=day,
                    manager=manager, recorded_by=manager,
                    status=DaroodEntry.Status.APPROVED, reviewed_at=now,
                )
                entries += 1

        # A few PENDING submissions from simple users addressed to manager1,
        # so the approval queue has something to show on first run.
        pending = 0
        for uname, amount, offset in [('user1', 200, 0), ('user2', 350, 1), ('user3', 120, 0)]:
            DaroodEntry.objects.create(
                user=created_users[uname], count=amount,
                date=today - timedelta(days=offset),
                manager=manager, recorded_by=created_users[uname],
                status=DaroodEntry.Status.PENDING,
            )
            pending += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded {len(DEMO_USERS)} users, {entries} approved and {pending} pending entries.'
        ))
        self.stdout.write(f'All demo passwords: "{PASSWORD}"')
        self.stdout.write('Superadmin login -> username: admin')
