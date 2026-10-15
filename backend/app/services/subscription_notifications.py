import logging
import smtplib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.email_service import send_email
from app.models import Notification, User

logger = logging.getLogger(__name__)


def queue_tenant_notification(
    db: Session,
    *,
    tenant_id: int,
    actor_id: int | None,
    notification_type: str,
    title: str,
    message: str,
    subscription_id: int | None,
) -> None:
    recipients = db.scalars(
        select(User).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
            User.is_admin.is_(False),
        )
    ).all()
    for recipient in recipients:
        db.add(
            Notification(
                recipient_id=recipient.id,
                actor_id=actor_id,
                type=notification_type,
                title=title,
                message=message,
                link="/subscriptions",
                entity_type="subscription",
                entity_id=subscription_id,
            )
        )


def send_tenant_subscription_email(
    db: Session,
    *,
    tenant_id: int,
    subject: str,
    message: str,
) -> int:
    if not settings.email_enabled:
        return 0
    recipients = db.scalars(
        select(User).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
            User.is_admin.is_(False),
        )
    ).all()
    failed = 0
    for recipient in recipients:
        try:
            send_email(recipient.email, subject, message)
        except (OSError, smtplib.SMTPException):
            failed += 1
            logger.exception(
                "Subscription email delivery failed for recipient_id=%s",
                recipient.id,
            )
    return failed
