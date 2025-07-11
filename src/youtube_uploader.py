# src/youtube_uploader.py

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Scopes for YouTube Data API v3
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Paths to client secrets and OAuth tokens (can be overridden via env vars)
CREDS_PATH = os.getenv('CREDS_PATH', 'credentials.json')
TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')


def get_youtube_service():
    """
    Returns an authenticated YouTube service instance, refreshing or
    prompting for OAuth as needed.
    """
    creds = None
    # Load existing credentials
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Refresh or complete OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            # For a CLI environment, run_console() is typically fine.
            creds = flow.run_console()
        # Save credentials for future runs
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

    # Build the service
    return build('youtube', 'v3', credentials=creds)


def upload_to_youtube(file_path: str,
                      title: str,
                      description: str,
                      thumbnail_path: str = None,
                      tags: list[str] = None) -> str:
    """
    Uploads the given video file to YouTube under the authenticated account.
    Returns the new video ID.
    """
    youtube = get_youtube_service()

    # 1) Prepare metadata
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': '23',  # e.g. 'People & Blogs'
        },
        'status': {
            'privacyStatus': 'public',
        }
    }

    # 2) Initiate resumable upload
    media = MediaFileUpload(
        file_path,
        chunksize=-1,   # let the client choose a sensible default
        resumable=True
    )
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    # 3) Upload loop with progress
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  -> YouTube upload progress: {pct}%")

    video_id = response.get('id')
    print(f"[+] YouTube video ID: {video_id}")

    # 4) Optional: set custom thumbnail, but swallow 403 errors
    if thumbnail_path:
        try:
            thumb_request = youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            )
            thumb_request.execute()
            print("  -> Thumbnail set")
        except HttpError as e:
            if e.resp.status == 403:
                print("  [!] Skipped setting thumbnail: permission denied")
            else:
                # re-raise any other error
                raise

    return video_id
