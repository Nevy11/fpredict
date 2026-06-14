from src.alerts.email_manager import EmailManager

def test_email():
    manager = EmailManager()
    manager.send_alert("Test Subject", "This is a test email from the FPredict platform.")

if __name__ == "__main__":
    test_email()
