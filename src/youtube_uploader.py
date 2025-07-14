import os
import json
from dataclasses import dataclass, field
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from src.ai_utils import suggest_hashtags

load_dotenv()

SCOPES = [
  "https://www.googleapis.com/auth/youtube.upload",
  "https://www.googleapis.com/auth/youtube.force-ssl"
]

def get_youtube_service() -> build:
    creds = None
    token_json = os.getenv("TOKEN_JSON")
    if token_json:
        info = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(info, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        creds_json = os.getenv("CREDS_JSON")
        if not creds_json:
            raise RuntimeError("CREDS_JSON not set in .env")
        client_cfg = json.loads(creds_json)
        flow = InstalledAppFlow.from_client_config(client_cfg, SCOPES)
        creds = flow.run_console()

    return build("youtube", "v3", credentials=creds)

@dataclass
class YouTubeUploader:
    default_tags: list[str] = field(default_factory=lambda: [
        "#shorts", "#reddit", "#redditstories"
    ])

    def upload(
        self,
        file_path: str,
        title: str,
        description: str,
        thumbnail_path: str | None = None
    ) -> str:
        # Suggest AI hashtags and merge with defaults
        ai_tags = suggest_hashtags(description)
        all_tags = [*ai_tags, *self.default_tags]

        # Build request
        youtube = get_youtube_service()
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": all_tags,
                "categoryId": "23",
            },
            "status": {"privacyStatus": "public"}
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        req = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        res = None
        while res is None:
            status, res = req.next_chunk()
            if status:
                print(f"  -> YouTube upload {int(status.progress() * 100)}%")

        vid = res.get("id")
        print(f"[+] YouTube video ID: {vid}")

        # Optional thumbnail
        if thumbnail_path:
            try:
                youtube.thumbnails().set(
                    videoId=vid,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("  -> Thumbnail set")
            except HttpError as e:
                if e.resp.status == 403:
                    print("  [!] Skipped thumbnail: no permission")
                else:
                    raise

        print("-> Using hashtags:", all_tags)
        return vid

def upload_to_youtube(
    file_path: str,
    title: str,
    description: str,
    thumbnail_path: str | None = None
) -> str:
    uploader = YouTubeUploader()
    return uploader.upload(file_path, title, description, thumbnail_path)