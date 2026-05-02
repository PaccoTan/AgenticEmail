import base64
import os
import tempfile
import time
import webbrowser

def preview_email_html(msg):
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    to = msg.get("To", "")
    cc = msg.get("Cc", "")

    # --- BODY (EmailMessage-safe way) ---
    html_part = msg.get_body(preferencelist=("html",))
    text_part = msg.get_body(preferencelist=("plain",))

    if html_part:
        body = html_part.get_content()
    elif text_part:
        body = f"<pre>{text_part.get_content()}</pre>"
    else:
        body = "<i>No content</i>"

    # --- ATTACHMENTS ---
    attachments_html = ""
    for att in msg.iter_attachments():
        filename = att.get_filename()
        ctype = att.get_content_type()
        main_type, subtype = ctype.split("/")
        if main_type == "image":
            img_bytes = att.get_content()
            if isinstance(img_bytes, str):
                img_bytes = img_bytes.encode()
            img_b64 = base64.b64encode(img_bytes).decode()
            attachments_html += f'<li><p>{filename}</p><img src="data:{ctype};base64,{img_b64}" style="max-width:200px;"></li>'
        elif subtype == "pdf":
            doc_bytes = att.get_content()
            if isinstance(doc_bytes, str):
                doc_bytes = doc_bytes.encode()
            doc_b64 = base64.b64encode(doc_bytes).decode()
            attachments_html += f"<li><a href=\"data:{ctype};base64,{doc_b64}\">{filename}</a></li>"
        else:
            attachments_html += f"<li>{filename}</li>"

    if not attachments_html:
        attachments_html = "<li>No attachments</li>"

    # --- HTML PAGE ---
    html = f"""
    <html>
    <head>
        <title>Email Preview</title>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .header {{ border-bottom: 1px solid #ccc; margin-bottom: 15px; }}
            .box {{ margin-top: 15px; }}
        </style>
    </head>
    <body>

        <div class="header">
            <h2>{subject}</h2>
            <p><b>From:</b> {sender}</p>
            <p><b>To:</b> {to}</p>
            <p><b>Cc:</b> {cc}</p>
        </div>

        <div class="box">
            {body}
        </div>

        <div class="box">
            <h3>Attachments</h3>
            <ul>{attachments_html}</ul>
        </div>

    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as f:
        f.write(html)
        webbrowser.open(f.name)

    time.sleep(5)
    os.remove(f.name)