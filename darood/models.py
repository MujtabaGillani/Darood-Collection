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
