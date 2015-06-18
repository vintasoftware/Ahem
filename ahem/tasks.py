from __future__ import unicode_literals

from django.utils import timezone

from ahem.utils import get_notification, get_backend, celery_is_available
from ahem.models import DeferredNotification, UserBackendRegistry

if celery_is_available():
    from celery import shared_task
else:
    def shared_task(func):
        return func


@shared_task
def dispatch_to_users(notification_name, eta=None, context={}, backends=None, **kwargs):
    notification = get_notification(notification_name)

    # TODO: if is periodic, schedule a execute_periodic_notification task
    # ScheduledNotification model
    # dispatch_to_users.apply_assync()

    users = notification.get_users(context)
    for user in users:
        for backend in backends:
            user_backend = UserBackendRegistry.objects.filter(user=user, backend=backend).first()

            if user_backend:
                deferred = DeferredNotification.objects.create(
                    notification=notification_name,
                    user_backend=user_backend,
                    context=context)

                if celery_is_available():
                    task_id = send_notification.apply_async((deferred.id,), eta=eta)
                    deferred.task_id = task_id
                    deferred.save()
                else:
                    send_notification(deferred.id)


@shared_task
def send_notification(deferred_id):
    deferred = ((DeferredNotification.objects
        .select_related('user_backend', 'user_backend__user'))
        .get(id=deferred_id))
    user = deferred.user_backend.user
    backend_settings = deferred.user_backend.settings

    backend = get_backend(deferred.user_backend.backend)
    notification = get_notification(deferred.notification)

    backend.send_notification(
        user, notification, deferred.context, backend_settings)

    deferred.ran_at = timezone.now()
    deferred.save()

