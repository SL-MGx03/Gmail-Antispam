from langchain_google_community.gmail.utils import build_resource_service,get_gmail_credentials
from langchain_google_community import GmailToolkit
import os

def get_gmail_toolkit():
    credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_sercret_file="credentials.json",
    )
    api_resource = build_resource_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit
