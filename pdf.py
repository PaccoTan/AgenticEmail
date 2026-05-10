import os
from weasyprint import HTML
from config import GENERATED_DOCUMENTS_FOLDER

def html_to_pdf(html_str,filename):
    path = os.path.join(GENERATED_DOCUMENTS_FOLDER, filename)
    HTML(string=html_str, base_url=".").write_pdf(path)
    return {
        "response": "The file was succesfully generated.",
        "link": f'<a href="http://127.0.0.1:5000/{GENERATED_DOCUMENTS_FOLDER}/{filename}">{filename}</a>'
    }
