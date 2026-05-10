from email.utils import getaddresses
import os
import mimetypes
import smtplib
import ssl
from display_email import preview_email_html
from email.message import EmailMessage
from dotenv import load_dotenv
import markdown
from config import UPLOAD_FOLDER
load_dotenv()

# Your Gmail credentials
email_address = os.getenv("GMAIL_ADDRESS")
app_password = os.getenv("GMAIL_PASSWORD")
MAX_SAFE_SIZE = 15 * 1024 * 1024  

# from email.message import EmailMessage

# reply = EmailMessage()
# reply["Subject"] = "Re: " + original["Subject"]
# reply["From"] = "you@gmail.com"
# reply["To"] = original["From"]

# orig_msg_id = original["Message-ID"]
# orig_refs = original.get("References", "")

# reply["In-Reply-To"] = orig_msg_id
# reply["References"] = (orig_refs + " " + orig_msg_id).strip()

# reply.set_content("Thanks for your email!")

from email_validator import validate_email, EmailNotValidError

def check_email(email):
    try:
        # Check syntax and deliverability (domain exists)
        email_info = validate_email(email, check_deliverability=True)
        return email_info.normalized
    except EmailNotValidError as e:
        print(f"Invalid: {e}")
        return False

def generate_msg(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] = [],
    bcc: list[str] = [],
    attachments: list[str] | None = None
):
    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    if len(cc) is not None:
        msg["Cc"] = ", ".join(cc)

    recipients = to + cc + bcc
    recipients = [check_email(e) for e in recipients]
    print(recipients)
    msg.set_content(body)
    msg.add_alternative(markdown.markdown(body,extensions=["extra", "codehilite", "nl2br"]),subtype="html")
    if attachments is not None:
        for file in attachments:
            attach_file(msg, file["filepath"], file["filename"])
    return msg, recipients

def get_type(path: str) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        maintype, subtype = "application", "octet-stream"
    else:
        maintype, subtype = mime_type.split("/")

    return maintype, subtype

def attach_file(msg: EmailMessage, path: str, filename: str):    
    maintype, subtype = get_type(path)
    with open(path, "rb") as f:
        file_data = f.read()
    
    msg.add_attachment(
        file_data,
        maintype=maintype,
        subtype=subtype,
        filename=filename 
    )

def send_msg(msg: EmailMessage, recipients: list[str], protocol="ssl"):
    msg_recipients = []
    for header in ["To", "Cc", "Bcc"]:
        if msg[header]:
            msg_recipients.extend(getaddresses([msg[header]]))
    msg_recipients = [email for _, email in msg_recipients]
    if sorted(msg_recipients) != sorted(recipients):
        raise ValueError("Recipients do not match header recipients.")
    if protocol == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            if len(msg.as_bytes()) > MAX_SAFE_SIZE:
                 raise ValueError("Email exceeds 20MB limit.")
            server.login(email_address, app_password)

            server.send_message(msg, to_addrs=recipients)
    else:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, app_password)
            server.send_message(msg, to_addrs=recipients)