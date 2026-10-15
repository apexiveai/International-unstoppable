from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Notification, Subscription
from app.services.subscription_notifications import (
    queue_tenant_notification,
    send_tenant_subscription_email,
)


def send_expiry_reminders(db: Session) -> tuple[int, int]:
    today = datetime.now(timezone.utc).date()
    subscriptions = db.scalars(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(
            Subscription.status == "active",
            Subscription.current_period_end.is_not(None),
        )
    ).all()
    sent = 0
    email_failures = 0
    for subscription in subscriptions:
        period_end = subscription.current_period_end
        if period_end is None:
            continue
        if period_end.tzinfo is not None:
            period_end = period_end.astimezone(timezone.utc).replace(tzinfo=None)
        days_remaining = (period_end.date() - today).days
        if days_remaining not in {3, 7}:
            continue
        notification_type = f"subscription_expiry_{days_remaining}d"
        already_sent = db.scalar(
            select(Notification.id)
            .where(
                Notification.type == notification_type,
                Notification.entity_type == "subscription",
                Notification.entity_id == subscription.id,
            )
            .limit(1)
        )
        if already_sent is not None:
            continue
        message = (
            f"Your {subscription.plan.name} subscription expires in "
            f"{days_remaining} days, on {period_end.date().isoformat()}."
        )
        queue_tenant_notification(
            db,
            tenant_id=subscription.tenant_id,
            actor_id=None,
            notification_type=notification_type,
            title=f"Subscription expires in {days_remaining} days",
            message=message,
            subscription_id=subscription.id,
        )
        db.commit()
        email_failures += send_tenant_subscription_email(
            db,
            tenant_id=subscription.tenant_id,
            subject=f"Your subscription expires in {days_remaining} days",
            message=message,
        )
        sent += 1
    return sent, email_failures
