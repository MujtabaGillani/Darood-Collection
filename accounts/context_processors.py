"""Template context processors."""


def pending_approvals(request):
    """Expose the count of darood submissions awaiting the current user.

    Used to show a badge on the navbar "Approvals" link for managers and
    superadmins. Returns 0 for everyone else.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.can_add_darood:
        return {'pending_approvals_count': 0}

    from darood.models import DaroodEntry

    qs = DaroodEntry.objects.filter(status=DaroodEntry.Status.PENDING)
    if not user.is_superadmin:
        qs = qs.filter(manager=user)
    return {'pending_approvals_count': qs.count()}
