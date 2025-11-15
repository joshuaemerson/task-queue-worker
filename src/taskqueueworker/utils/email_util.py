import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into environment variables

def send_email(subject: str, recipient: str, content: str):
    """
    Simple SMTP email client util

    Args:
        subject (str): The subject of the email to be sent
        recipient (str): The email address to which this email will be sent to
        content (str): The body of the email to be sent (plaintext)
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv('GMAIL_ADDRESS')
    msg["To"] = recipient
    msg.set_content(content)

    print(os.environ.get('GMAIL_ADDRESS'))

    # Ensures the connection is automatically closed afterward
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("GMAIL_ADDRESS").strip(),
                   os.getenv("GMAIL_APP_PASSWORD").strip())
        smtp.send_message(msg)
