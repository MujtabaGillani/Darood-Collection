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

        # Darood entries spread over the last ~40 days for the three simple users.
        manager = created_users['manager1']
        today = timezone.localdate()
        DaroodEntry.objects.all().delete()
        counts = {'user1': [100, 250, 300], 'user2': [500, 120], 'user3': [80, 400, 200, 150]}
        entries = 0
        for i in range(40):
            day = today - timedelta(days=i)
            for uname, amounts in counts.items():
                amount = amounts[i % len(amounts)]
                DaroodEntry.objects.create(
                    user=created_users[uname], count=amount, date=day, recorded_by=manager
                )
                entries += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded {len(DEMO_USERS)} users and {entries} darood entries.'
        ))
        self.stdout.write(f'All demo passwords: "{PASSWORD}"')
        self.stdout.write('Superadmin login -> username: admin')
