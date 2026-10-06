import smtplib

from email.message import EmailMessage

from app.core.config import settings

def send_email(

    to_email: str,

    subject: str,

    text_body: str,

) -> None:

    if not settings.email_enabled:

        print("")

        print("=" * 70)

        print("EMAIL DELIVERY DISABLED")

        print(f"TO: {to_email}")

        print(f"SUBJECT: {subject}")

        print(text_body)

        print("=" * 70)

        print("")

        return

    message = EmailMessage()

    message["From"] = (

        f"{settings.smtp_from_name} "

        f"<{settings.smtp_from_email}>"

    )

    message["To"] = to_email

    message["Subject"] = subject

    message.set_content(text_body)

    with smtplib.SMTP(

        settings.smtp_host,

        settings.smtp_port,

    ) as smtp:

        smtp.starttls()

        smtp.login(

            settings.smtp_username,

            settings.smtp_password,

        )

        smtp.send_message(message)