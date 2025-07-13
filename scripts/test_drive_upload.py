import os
from dotenv import load_dotenv
from src.drive_utils import get_drive_service
from googleapiclient.http import MediaFileUpload

# 1) Load .env into os.environ
load_dotenv()  

def upload_to_folder(local_path: str, folder_id: str) -> str:
    service = get_drive_service()

    # 2) Upload into root (default)
    media = MediaFileUpload(local_path, resumable=True)
    created = service.files().create(
        body={'name': os.path.basename(local_path)},
        media_body=media,
        fields='id, parents'
    ).execute()
    file_id = created['id']
    print(f"[+] Created file ID {file_id} with initial parents {created.get('parents')}")

    # 3) Move into your target folder, remove 'root'
    updated = service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents='root',
        fields='id, parents'
    ).execute()
    print(f"[+] Moved file into folder {folder_id}. New parents: {updated.get('parents')}")

    return file_id

if __name__ == "__main__":
    # 4) Read folder ID now that .env is loaded
    folder_id = os.getenv("DRIVE_OUTPUTS_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("Set DRIVE_OUTPUTS_FOLDER_ID in your .env")

    # 5) Create a tiny dummy file
    test_file = "test.txt"
    with open(test_file, "w") as f:
        f.write("hello, drive")

    # 6) Upload & move
    file_id = upload_to_folder(test_file, folder_id)
    print(f"[+] Uploaded {test_file} as file ID: {file_id}")
