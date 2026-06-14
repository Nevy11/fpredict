import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

class EmailManager:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")

    def send_alert(self, subject, body):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.smtp_user
        msg['To'] = self.smtp_user # Send to self for now

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            print("Alert sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")
