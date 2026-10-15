from app.database import SessionLocal
from app.services.subscription_reminders import send_expiry_reminders


def main() -> None:
    with SessionLocal() as db:
        sent, email_failures = send_expiry_reminders(db)
    print(
        f"Subscription reminders processed: {sent}; "
        f"email delivery failures: {email_failures}"
    )


if __name__ == "__main__":
    main()
