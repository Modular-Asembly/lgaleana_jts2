import os
import base64
from email.mime.text import MIMEText
from typing import Dict

from googleapiclient.discovery import build
from google.auth.credentials import Credentials
from app.core.google_auth.google_auth import get_google_oauth_credentials


def create_email_message(sender: str, to: str, subject: str, body: str) -> Dict[str, str]:
    """
    Creates a raw email message for Gmail API.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: Subject of the email.
        body: Body text of the email.

    Returns:
        A dictionary containing the raw email message ready for the Gmail API.
    """
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    # Gmail API requires base64url encoded string.
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw_message}


def send_email_report(success_count: int, failed_count: int, report_url: str) -> Dict[str, str]:
    """
    Sends an email using the Gmail API containing the report link of the Google Sheets document.

    The email summarizes the successful and failed upload counts and includes the URL of the report.
    Relies on Google OAuth credentials from the google_auth module.

    Environment Variables:
        GMAIL_SENDER: Sender's email address.
        GMAIL_RECIPIENT: Recipient's email address.
        GMAIL_EMAIL_SUBJECT: Subject line for the email (optional, default provided).

    Args:
        success_count: Number of successful uploads.
        failed_count: Number of failed uploads.
        report_url: URL string of the Google Sheets report.

    Returns:
        A dictionary with keys 'status' and 'message' indicating the result of the email delivery.
    
    Raises:
        googleapiclient.errors.HttpError: When the Gmail API call fails.
    """
    gmail_sender = os.getenv("GMAIL_SENDER")
    gmail_recipient = os.getenv("GMAIL_RECIPIENT")
    email_subject = os.getenv("GMAIL_EMAIL_SUBJECT", "Upload Report Notification")

    if not gmail_sender or not gmail_recipient:
        raise EnvironmentError("GMAIL_SENDER and GMAIL_RECIPIENT environment variables must be set.")

    # Prepare the email body
    email_body = (
        f"Hello,\n\n"
        f"Please find the upload report details below:\n"
        f"Successful Uploads: {success_count}\n"
        f"Failed Uploads: {failed_count}\n"
        f"Report URL: {report_url}\n\n"
        f"Best regards,\n"
        f"Your Pipeline Service"
    )

    message = create_email_message(gmail_sender, gmail_recipient, email_subject, email_body)

    # Get credentials from our google_auth module
    creds: Credentials = get_google_oauth_credentials()

    # Build the Gmail service
    service = build("gmail", "v1", credentials=creds)

    # Send the message using the Gmail API
    sent_message = service.users().messages().send(userId="me", body=message).execute()
    return {"status": "success", "message": f"Email sent successfully, id: {sent_message.get('id')}"}
