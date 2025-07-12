# scripts/list_backgrounds.py

import os
from dotenv import load_dotenv
from src.drive_utils import get_drive_service

load_dotenv()

folder_id = os.getenv("DRIVE_BACKGROUNDS_FOLDER_ID")
service   = get_drive_service()

resp = service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="files(id, name)"
).execute()

files = resp.get('files', [])
print(f"Found {len(files)} files in folder {folder_id}:")
for f in files:
    print(f" • {f['name']} (ID {f['id']})")
