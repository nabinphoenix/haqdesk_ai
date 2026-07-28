from app.services.email_service import send_email

result = send_email(
    to_email="juniorjkberlin@gmail.com",
    subject="Test Email from HaqDesk AI",
    html_body="<h1>It works!</h1><p>This is a test email from HaqDesk AI SMTP setup.</p>"
)
print(f"Email sent: {result}")