import imaplib
import os
import email
from dotenv import load_dotenv
from email.utils import getaddresses, parsedate_to_datetime
from operator import itemgetter
import json
load_dotenv()


mail = imaplib.IMAP4_SSL("imap.gmail.com")
email_address = os.getenv("GMAIL_ADDRESS")
app_password = os.getenv("GMAIL_PASSWORD")


# From:
# To:
# Cc:
# Subject:
# Date:
# Message-ID:
# Routing / delivery metadata
# Received:
# Return-Path:
# Delivered-To:
# Reply-To:

def load_contacts():
    try:
        with open('data/contacts.json', 'r') as f:
            contacts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        contacts = {}
    return contacts

def fetch_emails(email_ids, batch_size=100):
    msgs = []
    for i in range(0, len(email_ids), batch_size):
        batch = email_ids[i:i+batch_size]
        status, msg_data = mail.uid(
            "fetch",
            b",".join(batch),
            "(BODY.PEEK[HEADER.FIELDS (FROM TO CC DATE)])"
        )
        msgs.extend(msg_data)
    return msgs

def get_last_uid(mailbox="inbox"):
    with open('data/metadata.json', 'r') as file:
        data = json.load(file)
    if mailbox in data and 'last_uid' in data[mailbox]:
        result = data[mailbox]['last_uid']
        return result
    return ""

def get_contacts(batch_size=100):
    mail.login(email_address,app_password)
    mailboxes = ['INBOX']
    status, boxes = mail.list()
    if status == "OK":
        for box in boxes:
            decoded = box.decode()
            if '\\Sent' in decoded:
                mailbox_name = decoded.split(' "/" ')[-1].strip('"')
                mailboxes.append(mailbox_name)
    contacts = load_contacts()
    NO_CONTACTS = len(contacts)
    UPDATE_CONTACTS= False
    for mailbox in mailboxes:
        status, _ = mail.select(f'"{mailbox}"')
        if status != "OK":
            print(f"Failed to select {mailbox} with status {status}")
            continue

        last_uid = get_last_uid(mailbox)
        if NO_CONTACTS or last_uid == "":
            _, messages =  mail.uid("search", None, f"SINCE 01-Jan-2025")
            email_ids = messages[0].split()
            email_ids = sorted(email_ids, key=int)[-1000:]
        else:
            _, messages =  mail.uid("search", None, f"UID {last_uid}:*")
            email_ids = messages[0].split()
            email_ids = sorted(email_ids, key=int)

        msg_data = fetch_emails(email_ids, batch_size=100)
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                date = parsedate_to_datetime(msg["Date"]).isoformat()
                for field in ["From", "To", "Cc"]:
                    if msg[field]:
                        for name, addr in getaddresses([msg[field]]):
                            addr = addr.lower()
                            if "no-reply" in addr or "noreply" in addr or addr == email_address.lower():
                                continue
                            if addr in contacts:
                                contacts[addr] = (addr, name, date, contacts[addr][-1] + 1)
                            else:
                                contacts[addr] = (addr, name, date, 1)

    with open('data/contacts.json',"w") as f:
        json.dump(contacts, f,indent=4)
    return contacts

get_contacts()