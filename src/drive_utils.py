# src/drive_utils.py

import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from .config import settings

# These are the scopes you must have in your token.json:
DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file', # upload into your outputs folder
    'https://www.googleapis.com/auth/drive.readonly', # download background clips
    'https://www.googleapis.com/auth/drive.metadata.readonly', # list folder contents
]

TOKEN_PATH = settings.TOKEN_PATH  # e.g. "token.json"

def get_drive_service():
    creds = None

    # 1) Load existing credentials (now re-associate the Drive scopes)
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, DRIVE_SCOPES)

    # 2) Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # 3) If we still don’t have valid creds, ask user to reprovision
    if not creds or not creds.valid:
        raise RuntimeError(
            "No valid Drive credentials.  \n"
            "Please run your `refresh_token.py` (with DRIVE + YT scopes) to reprovision token.json."
        )

    return build('drive', 'v3', credentials=creds)

def upload_to_drive(local_path: str) -> str:
    service = get_drive_service()

    media = MediaFileUpload(
        local_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024
    )

    req = service.files().create(
        body={
            "name": os.path.basename(local_path),
            "parents": [settings.DRIVE_OUTPUTS_FOLDER_ID]
        },
        media_body=media,
        fields="id"
    )

    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  → Drive upload progress: {pct}%")
    return resp["id"]
