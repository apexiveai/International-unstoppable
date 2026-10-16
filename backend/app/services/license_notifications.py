import logging
import smtplib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.email_service import send_email
from app.models import License, LicenseEvent, Notification, User

logger = logging.getLogger(__name__)


def send_license_renewal_reminders(db: Session, *, actor_user_id: int) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    today = now.date()
    licenses = db.scalars(
        select(License)
        .where(License.status == "active")
        .order_by(License.expires_at)
    ).all()
    notified_licenses = 0
    notification_count = 0
    email_attempts = 0
    email_failures = 0

    for license in licenses:
        expires_at = license.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            continue
        expiry_date = expires_at.astimezone(timezone.utc).date()
        days_remaining = (expiry_date - today).days
        if days_remaining < 0 or days_remaining > 30:
            continue
        reminder_window = 3 if days_remaining <= 3 else 7 if days_remaining <= 7 else 30
        expiry_key = expiry_date.isoformat()

        previous_reminders = db.scalars(
            select(LicenseEvent).where(
                LicenseEvent.license_id == license.id,
                LicenseEvent.event_type == "renewal_reminder_sent",
            )
        ).all()
        if any(
            event.details.get("expires_on") == expiry_key
            and event.details.get("reminder_window") == reminder_window
            for event in previous_reminders
        ):
            continue

        recipients = db.scalars(
            select(User).where(
                User.tenant_id == license.tenant_id,
                User.is_active.is_(True),
                User.is_admin.is_(False),
            )
        ).all()
        message = (
            f"Your RPA license expires on {expiry_key}. "
            "Please contact your administrator to renew it and avoid interruption."
        )
        for recipient in recipients:
            db.add(
                Notification(
                    recipient_id=recipient.id,
                    actor_id=actor_user_id,
                    type=f"license_expiry_{reminder_window}d",
                    title="RPA license renewal reminder",
                    message=message,
                    link="/dashboard",
                    entity_type="license",
                    entity_id=license.id,
                )
            )
            notification_count += 1
            if settings.email_enabled:
                email_attempts += 1
                try:
                    send_email(
                        recipient.email,
                        "Your RPA license is nearing expiration",
                        message,
                    )
                except (OSError, smtplib.SMTPException):
                    email_failures += 1
                    logger.exception(
                        "RPA license renewal email failed for recipient_id=%s",
                        recipient.id,
                    )

        db.add(
            LicenseEvent(
                license_id=license.id,
                actor_user_id=actor_user_id,
                event_type="renewal_reminder_sent",
                details={
                    "expires_on": expiry_key,
                    "days_remaining": days_remaining,
                    "reminder_window": reminder_window,
                    "notifications_created": len(recipients),
                    "email_attempts": len(recipients) if settings.email_enabled else 0,
                },
            )
        )
        notified_licenses += 1

    db.commit()
    return {
        "licenses_notified": notified_licenses,
        "notifications_created": notification_count,
        "email_attempts": email_attempts,
        "email_failures": email_failures,
    }
