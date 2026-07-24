from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DaroodEntry(models.Model):
    """A logged count of Darood Shareef for a user on a given date.

    Two ways an entry is created:

    * A **simple user** submits their own count and picks a manager to review
      it. The entry starts as ``PENDING`` and only counts once the manager
      **approves** it.
    * A **manager / superadmin** records a count directly (search flow). That
      entry is ``APPROVED`` immediately since a trusted user entered it.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='darood_entries',
        help_text='The person this darood count belongs to.',
    )
    count = models.PositiveIntegerField(help_text='How many darood were recited.')
    date = models.DateField(help_text='The day this count is for.')

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # The manager responsible for reviewing / who reviewed this entry.
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_entries',
    )

    # Audit trail.
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_entries',
        help_text='Who created this entry (the submitter or the manager).',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['manager', 'status']),
        ]
        verbose_name = 'Darood entry'
        verbose_name_plural = 'Darood entries'

    def __str__(self):
        return f'{self.user} — {self.count} on {self.date} ({self.status})'

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING


class ReserveTransaction(models.Model):
    """A movement in a manager's private darood **reserve** ledger.

    A reserve is a manager's personal stash of darood that is invisible to
    admins and does **not** count toward any total until it is submitted.

    Two kinds of movement:

    * ``ADD``    — the manager stashes darood into their reserve (a quantity on
      a chosen date). No :class:`DaroodEntry` is created, so it stays private
      and uncounted.
    * ``SUBMIT`` — the manager releases part of their reserve into the public
      record. This creates an ``APPROVED`` :class:`DaroodEntry` for the manager
      (visible to admins, counted like any recorded darood) and decrements the
      reserve balance.

    The current balance is ``sum(ADD.count) - sum(SUBMIT.count)`` for a manager.
    """

    class Kind(models.TextChoices):
        ADD = 'add', _('Added to reserve')
        SUBMIT = 'submit', _('Submitted from reserve')

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reserve_transactions',
        help_text='The manager who owns this reserve.',
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    count = models.PositiveIntegerField(help_text='How many darood this movement is for.')
    date = models.DateField(help_text='The day this reserve movement is for.')

    # For SUBMIT movements: the public entry that was created when releasing
    # darood from the reserve. Null for ADD movements.
    entry = models.ForeignKey(
        'DaroodEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserve_submission',
        help_text='The approved entry created when reserve darood was submitted.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['manager', 'kind']),
            models.Index(fields=['manager', '-created_at']),
        ]
        verbose_name = 'Reserve transaction'
        verbose_name_plural = 'Reserve transactions'

    def __str__(self):
        return f'{self.manager} {self.kind} {self.count} ({self.date})'
