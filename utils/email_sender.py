import smtplib
from email.message import EmailMessage

def send_email(to_list, subject, body):
    EMAIL_ADDRESS = "daniel_delrio@hotmail.es"
    EMAIL_PASSWORD = "TU_APP_PASSWORD"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(to_list)
    msg.set_content(body)

    with smtplib.SMTP("smtp.office365.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
