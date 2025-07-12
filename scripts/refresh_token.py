from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

SCOPES = [
  'https://www.googleapis.com/auth/drive.file',                # upload to outputs folder
  'https://www.googleapis.com/auth/drive.readonly',            # download clips
  'https://www.googleapis.com/auth/drive.metadata.readonly',   # list folder contents
  'https://www.googleapis.com/auth/youtube.upload'             # upload videos
]

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    print("token.json created/updated")

if __name__ == '__main__':
    main()
