<<<<<<< HEAD
# src/asset_manager.py

=======
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
import os
import random
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
<<<<<<< HEAD
=======
import io
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790

from .drive_utils import get_drive_service

load_dotenv()

def choose_and_stream_video() -> tempfile.NamedTemporaryFile:
    """
<<<<<<< HEAD
    Pick a random clip from DRIVE_BACKGROUNDS_FOLDER_ID and stream it
    into a temp file. Uses 8 MiB chunks, retries up to 3 times per chunk,
    and logs progress every 5 chunks (~40 MiB).
=======
    List all clips in DRIVE_BACKGROUNDS_FOLDER_ID, pick one randomly,
    stream-download it to a temp file, and return that NamedTemporaryFile.
    Retries transient failures up to 5 times per chunk.
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
    """
    folder_id = os.getenv("DRIVE_BACKGROUNDS_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("Set DRIVE_BACKGROUNDS_FOLDER_ID in your .env")

    service = get_drive_service()
<<<<<<< HEAD
=======
    # list all non-trashed files in that folder
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
    resp = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
<<<<<<< HEAD
=======

>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
    files = resp.get('files', [])
    if not files:
        raise RuntimeError(f"No files found in Drive folder {folder_id}")

    choice = random.choice(files)
    file_id = choice['id']
<<<<<<< HEAD
    name    = choice['name']
    suffix  = Path(name).suffix or ".mp4"

    tmp = tempfile.NamedTemporaryFile(prefix="bg_", suffix=suffix, delete=False)
    print(f"[+] Streaming background “{name}” -> {tmp.name}")

    # Open with default buffering
    with open(tmp.name, "wb") as fh:
        downloader = MediaIoBaseDownload(
            fh,
            service.files().get_media(fileId=file_id),
            chunksize=8 * 1024 * 1024  # 8 MiB
        )

        done = False
        chunk_count = 0
        while not done:
            for attempt in range(1, 4):  # up to 3 retries per chunk
                try:
                    status, done = downloader.next_chunk()
                    break
                except (TimeoutError, HttpError) as e:
                    print(f"    Warning: chunk download failed (attempt {attempt}/3): {e}")
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)

            chunk_count += 1
            # log every 5 chunks (~40 MiB)
            if chunk_count % 5 == 0 and status:
                pct = int(status.progress() * 100)
                print(f"    Download progress: {pct}%")

=======
    name = choice['name']
    suffix = Path(name).suffix or ".mp4"

    tmp = tempfile.NamedTemporaryFile(prefix="bg_", suffix=suffix, delete=False)
    fh = io.FileIO(tmp.name, mode='wb')

    # Use a smaller chunk size to avoid long socket reads
    downloader = MediaIoBaseDownload(
        fh,
        service.files().get_media(fileId=file_id),
        chunksize=1 * 1024 * 1024  # 1 MiB
    )

    done = False
    print(f"[+] Streaming background “{name}” → {tmp.name}")

    # Download loop with retries
    max_retries = 3
    last_pct = 0
    while not done:
        for attempt in range(1, max_retries + 1):
            try:
                status, done = downloader.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    if pct // 5 != last_pct // 5:
                        print(f"    Download progress: {pct}%")
                        last_pct = pct
                break
            except (TimeoutError, HttpError) as e:
                print(f"    Warning: chunk download failed (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    fh.close()
                    tmp.close()
                    raise
                # exponential backoff before retrying
                time.sleep(2 ** attempt)

    fh.close()
>>>>>>> 17685057621a0121991a0d4b6dffac46484a7790
    return tmp
