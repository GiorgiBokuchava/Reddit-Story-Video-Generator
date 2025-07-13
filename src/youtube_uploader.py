import os, json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_youtube_service():
    creds = None

    token_json = os.getenv('TOKEN_JSON')
    if token_json:
        info = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(info, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        creds_json = os.getenv('CREDS_JSON')
        if not creds_json:
            raise RuntimeError("CREDS_JSON not set in env")
        client_cfg = json.loads(creds_json)
        flow = InstalledAppFlow.from_client_config(client_cfg, SCOPES)
        creds = flow.run_console()

    return build('youtube','v3', credentials=creds)

def upload_to_youtube(
    file_path: str,
    title: str,
    description: str,
    thumbnail_path: str = None,
    tags: list[str] = None
) -> str:
    youtube = get_youtube_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': '23',
        },
        'status': {'privacyStatus': 'public'}
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    req = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    res = None
    while res is None:
        status, res = req.next_chunk()
        if status:
            print(f"  → YouTube upload {int(status.progress()*100)}%")

    vid = res.get('id')
    print(f"[+] YouTube video ID: {vid}")

    if thumbnail_path:
        try:
            youtube.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("  → Thumbnail set")
        except HttpError as e:
            if e.resp.status == 403:
                print("  [!] Skipped thumbnail: no permission")
            else:
                raise

    return vid
