import os
import requests
from dotenv import load_dotenv
from flask import current_app

load_dotenv()

API_KEY = os.getenv("BREVO_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
FROM_NAME = os.getenv("FROM_NAME")

def send_email_to_all_clients(subject, content, recipients):
    """
    שולח מייל לכל הלקוחות הרשומים ברשימת recipients
    """
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    for recipient in recipients:
        data = {
            "sender": {"name": FROM_NAME, "email": FROM_EMAIL},
            "to": [{"email": recipient}],
            "subject": subject,
            "htmlContent": f"<html><body>{content}</body></html>"
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code >= 400:
            current_app.logger.error(f"שליחת מייל ל-{recipient} נכשלה: {response.text}")
