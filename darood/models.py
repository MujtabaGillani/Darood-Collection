from django.conf import settings
from django.db import models


class DaroodEntry(models.Model):
    """A single logged count of Darood Shareef for a user on a given date."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='darood_entries',
        help_text='The person this darood count belongs to.',
    )
    count = models.PositiveIntegerField(help_text='How many darood were recited.')
    date = models.DateField(help_text='The day this count is for.')

    # Audit trail: who actually recorded the entry (a manager / superadmin).
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['user', 'date']),
        ]
        verbose_name = 'Darood entry'
        verbose_name_plural = 'Darood entries'

    def __str__(self):
        return f'{self.user} — {self.count} on {self.date}'
