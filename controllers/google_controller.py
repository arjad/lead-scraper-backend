import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_auth_url():
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}. Please ensure it exists.")
        
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE, SCOPES, redirect_uri="http://localhost:8000/auth/google/callback"
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url

def exchange_code(code: str):
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE, SCOPES, redirect_uri="http://localhost:8000/auth/google/callback"
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    with open(TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())
        
    return True

def send_email(to_email: str, subject: str, content: str):
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Not authenticated with Google. Please visit /google/login first.")
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    service = build('gmail', 'v1', credentials=creds)
    message = EmailMessage()
    
    message.set_content(content)
    message['To'] = to_email
    message['From'] = "me"
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {
        'raw': encoded_message
    }
    
    send_message = (service.users().messages().send(userId="me", body=create_message).execute())
    return send_message
