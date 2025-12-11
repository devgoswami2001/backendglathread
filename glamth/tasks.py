import json
from celery import shared_task
from django.conf import settings
from pywebpush import webpush, WebPushException
from .models import PushSubscription


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_push_to_subscription(self, sub_id, payload):
    """
    Send a push notification to a single subscription.
    Automatically retries transient errors.
    Removes subscription if endpoint is expired.
    """

    try:
        sub = PushSubscription.objects.get(id=sub_id)

        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth,
            },
        }

        # Send push
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY"],
            vapid_claims=settings.WEBPUSH_SETTINGS["VAPID_CLAIMS"],
            timeout=10,
        )

        return True

    except PushSubscription.DoesNotExist:
        # Subscription already deleted
        return False

    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)

        # Endpoint expired → delete subscription
        if status in (404, 410):
            try:
                sub.delete()
            except:
                pass
            return False

        # Temporary network error → retry
        raise self.retry(exc=exc)

    except Exception as exc:
        # Unknown error → retry
        raise self.retry(exc=exc)
