import smtplib
from email.message import EmailMessage
from typing import Optional

from ..config import EMAIL_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM


def send_invoice_email_if_enabled(to_email: str, pdf_bytes: bytes, invoice_code: str) -> Optional[str]:
    if not EMAIL_ENABLED:
        return None
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and EMAIL_FROM):
        return None

    msg = EmailMessage()
    msg["Subject"] = f"Your Invoice {invoice_code}"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg.set_content("Thank you for shopping! Your invoice is attached.")

    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"invoice_{invoice_code}.pdf")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    return "sent"

