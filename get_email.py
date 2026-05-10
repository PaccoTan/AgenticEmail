import imaplib
import os
import email
from dotenv import load_dotenv
from email.utils import getaddresses, parsedate_to_datetime
from operator import itemgetter
import json
from pathlib import Path
from flask import current_app
from config import DATA_FOLDER
load_dotenv()


mail = imaplib.IMAP4_SSL("imap.gmail.com")
email_address = os.getenv("GMAIL_ADDRESS")
app_password = os.getenv("GMAIL_PASSWORD")
if mail.state not in ("AUTH", "SELECTED"):
    mail.login(email_address, app_password)

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
    path = Path(f"{DATA_FOLDER}/contacts.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    try:
        with open(f'{DATA_FOLDER}/contacts.json', 'r') as f:
            contacts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        contacts = {}
    return contacts

def save_contacts(contacts):
    with open(f'{DATA_FOLDER}/contacts.json', "w") as f:
        json.dump(contacts,f, indent=4)

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
    path = Path(f"{DATA_FOLDER}/metadata.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w") as f:
            json.dump({}, f, indent=4)
    with open(f'{DATA_FOLDER}/metadata.json', 'r') as file:
        data = json.load(file)
    if mailbox in data and 'last_uid' in data[mailbox]:
        result = data[mailbox]['last_uid']
        return result
    return ""

def update_last_uid(email_id, mailbox="inbox"):
    path = Path(f"{DATA_FOLDER}/metadata.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w") as f:
            json.dump({}, f, indent=4)
    with open(f'{DATA_FOLDER}/metadata.json', 'r') as file:
        data = json.load(file)
    if mailbox not in data:
        data[mailbox] = {}
    data[mailbox]['last_uid'] = email_id.decode()
    with open(f'{DATA_FOLDER}/metadata.json', 'w') as file:
        json.dump(data,file, indent=4)

def retrieve_contacts(batch_size=100):
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
        
        if len(email_ids) == []:
            continue

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
        update_last_uid(email_ids[-1],mailbox)
    save_contacts(contacts)
    return contacts

def get_contacts(client,model,query,n=10):
    if n > 50:
        return {"error": "Requested for more than 50 matches."}
    contacts = retrieve_contacts().values()
    messages = [{
        "role": "system",
        "content": "You are a contact-matching system. Your task is to return the top N most relevant contacts from a provided list based on a user query.\n\nEach contact is a tuple:\n(email, name, mostRecentContactDate, occurrences)\n\nYour job is to rank contacts by relevance to the query.\n\nMatching guidelines:\n1. Name similarity is the most important factor (exact match > partial match > fuzzy match).\n2. Email relevance provides secondary signal (prefix or domain overlap with query).\n3. Recency matters: more recent mostRecentContactDate increases relevance.\n4. Occurrences indicate relationship strength and should increase ranking.\n5. Interpret query intent: if it looks like a person name, prioritize name matching; if it looks like an email/domain, prioritize email matching.\n\nTie-breaking:\n- Higher occurrences first\n- More recent contact date second\n- Lexicographically earlier email last\n\nOutput requirements:\n- Return exactly N results if available, otherwise return all matches.\n- Each result must include: email, name, score (0–1), and a short reason (1–2 sentences).\n- Do not fabricate or modify contacts.\n\nReturn results sorted from most to least relevant."
    },{
        "role": "user",
        "content": f"Query: {query}\nN: {n}\nContacts: {contacts}"
    }]

    schema = {
        "name": "rank_contacts",
        "description": "Ranks contacts by relevance to a query",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
            "results": {
                "type": "array",
                "items": {
                "type": "object",
                "properties": {
                    "email": { "type": "string" },
                    "name": { "type": "string" },
                    "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                    },
                    "reason": { "type": "string" }
                },
                "required": ["email", "name", "score", "reason"],
                "additionalProperties": False
                }
            }
            },
            "required": ["results"],
            "additionalProperties": False
        }
    }
    response = client.chat.completions.create(
        model= model,
        messages=messages,
        temperature=0, 
        response_format={"type":"json_schema", "json_schema": schema} 
    )
    result = json.loads(response.choices[0].message.content)
    return result