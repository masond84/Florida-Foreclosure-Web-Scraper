# Include Modules
import smtplib
import schedule
import pytz
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


# Specify the email configuration
smtp_server = "smtp.gmail.com"  # Use the appropriate SMTP server
smtp_port = 587  # Use the appropriate SMTP port
sender_email = "dev.rmason@gmail.com"  # Your email address
sender_password = "yfdtdxlcwemakjvi"  # Your email password
#recipients = []
recipient_emails = ["devin.mason@spartans.ut.edu", "jackson@serrallesgroup.com"]  # List of recipients
# Timezone config
timezone = "America/New_York"

def send_email(subject, message, attachment_paths):
    # Create the email content
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, "plain"))

    # Attach the Excel files
    for attachment_path in attachment_paths:
        with open(attachment_path, "rb") as attachment_file:
            attachment = MIMEApplication(attachment_file.read(), _subtype="xlsx")
            attachment.add_header(
                "content-disposition",
                "attachment",
                filename=attachment_path.split("\\")[-1],
            )
            msg.attach(attachment)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())
