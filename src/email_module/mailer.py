"""Отправка email через SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mailer:
    def __init__(self, host: str, port: int, username: str, password: str, sender_name: str, sender_email: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender_name = sender_name
        self.sender_email = sender_email

    def send(self, to: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL(self.host, self.port) as server:
            server.login(self.username, self.password)
            server.sendmail(self.sender_email, to, msg.as_string())
