import os, json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .config import settings

DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
]

def get_drive_service():
    token_json = os.getenv('TOKEN_JSON')
    if not token_json:
        raise RuntimeError("TOKEN_JSON not set in env")
    info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(info, DRIVE_SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError("Drive credentials invalid—please refresh TOKEN_JSON")

    return build('drive','v3', credentials=creds)

def upload_to_drive(local_path: str) -> str:
    service = get_drive_service()
    media = MediaFileUpload(local_path, mimetype="video/mp4", resumable=True)
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
            print(f"  → Drive upload {int(status.progress()*100)}%")
    return resp["id"]
