# AI Powered Email Automation

## Overview

AI Powered Email Automation is an intelligent email assistant designed to streamline email management and document generation using Large Language Models (LLMs). The application helps users reduce time spent reading, organizing, drafting, and sending emails by integrating an LLM-powered agent with email tools and document generation capabilities.

This project was developed as the final project for **CSC 7644: Applied LLM Development**.

The system leverages OpenAI’s GPT-4o-mini model alongside a Flask-based web application to provide a supervised AI assistant capable of drafting emails, managing contacts, generating documents, and assisting with productivity-focused workflows.

---

## Key Features

- AI-assisted email drafting and response generation
- Email sending with support for:
  - To, CC, and BCC recipients
  - Attachments
  - Subject and body generation
- User confirmation workflow before sending emails
- Contact retrieval and matching using IMAP
- Intelligent contact suggestions with ranking and justification
- HTML and PDF document generation using Markdown and WeasyPrint
- Flask-based web interface for interacting with the AI agent
- Attachment integration within generated documents
- Provider-agnostic email support using SMTP and IMAP
- Conversation and tool interaction tracking for debugging and development

---

## Tech Stack

### LLM and APIs

- **OpenAI API**
  - Utilized for LLM-based reasoning and generation
- **GPT-4o-mini**
  - Primary language model used for the AI agent

### Backend

- **Python**
  - Core programming language for the entire application
- **Flask**
  - Web framework used for both frontend serving and backend API handling

### Email Handling

- **smtplib**
  - Used for sending emails through SMTP
- **email (Python standard library)**
  - Used for constructing email messages
- **imaplib**
  - Used for retrieving emails and contact metadata through IMAP

### Document Generation

- **Markdown**
  - Used for document formatting
- **WeasyPrint**
  - Converts generated HTML into PDF documents

---

## High-Level Architecture

### Frontend

The frontend is built using Flask templates and provides a lightweight web interface for users to communicate with the AI assistant, review generated content, and confirm email actions before sending.

### Backend Agent System

The backend manages:

- User-agent interactions
- Tool calling and execution
- Conversation history tracking
- Email construction and transmission
- Document generation workflows

The AI agent uses GPT-4o-mini to reason through user requests and determine when to invoke backend tools.

### Email Services

The application integrates directly with email providers using standard protocols:

- **SMTP** for sending emails
- **IMAP** for retrieving email metadata and contacts

This provider-agnostic approach allows compatibility with multiple email services such as Gmail and Outlook.

### Document Generation Pipeline

Generated documents are first created in HTML/Markdown format and then converted into PDFs using WeasyPrint. Attachments and uploaded assets can also be embedded into generated documents.

---

## Setup

Conda must be used to install weasyprint as it will handle dependencies that are outside of pip.
Windows and python 3.12 was used during developmen, so use these to ensure reproducibility. 
Currently the system is used with GMAIL, but it can be easily adapted to any email service.

1. conda install -c conda-forge weasyprint
2. pip install requirements.txt

To setup environment variables, copy and replace the fields in the .env.example provided.

App Password must be generated for email automation.
Here is a guide on how to generate an app password for Gmail. https://support.google.com/mail/answer/185833?hl=en

---

## Running the Application

- python app.py

---

## Repository Organization

- app.py main application logic
- extensions.py stores the websocket for the webapp
- config.py specifies and creates subfolders necessary
- static/ CSS/JS for the frontend
- templates/ HTML for the frontend
- agent.py main agent loop as well as tool schemas
- send_email.py contains function that generates and sends emails
- get_email.py contains code that manages email retrieval for contacts
- display_email.py creates a html preview of email message
- pdf.py converts html to pdf
---
## Author

**Pacco Tan**  
CSC 7644 — Applied LLM Development

# Requirements
# pip install openai flask flask-socketio dotenv email-validator jsonschema markdown
# 

