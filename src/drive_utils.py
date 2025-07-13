<<<<<<< HEAD
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
            "parents": [settings.drive_outputs_folder_id]
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
=======
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import settings

CREDS_PATH = settings.CREDS_PATH
TOKEN_PATH = settings.TOKEN_PATH
SCOPES = [
    'https://www.googleapis.com/auth/drive.file', # for upload-to-folder
    'https://www.googleapis.com/auth/drive.readonly', # to list/background clips
]

def get_drive_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(local_path: str, folder_id: str | None = None) -> str:
    service = get_drive_service()
    # default to DRIVE_OUTPUTS_FOLDER_ID if not passed
    if folder_id is None:
        folder_id = os.getenv("DRIVE_OUTPUTS_FOLDER_ID")
        if not folder_id:
            raise RuntimeError("Set DRIVE_OUTPUTS_FOLDER_ID in your .env")

    # upload into root
    media = MediaFileUpload(local_path, resumable=True)
    created = service.files().create(
        body={'name': os.path.basename(local_path)},
        media_body=media,
        fields='id, parents'
    ).execute()
    file_id = created['id']

    # move into outputs folder, remove root parent
    updated = service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents='root',
        fields='id, parents'
    ).execute()

    print(f"[+] Uploaded {local_path} → Drive file ID: {file_id} in folder {folder_id}")
    return file_id
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
