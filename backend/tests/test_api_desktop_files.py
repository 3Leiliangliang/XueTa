import hashlib
import uuid
from pathlib import Path

from app.api.v1 import files as files_api
from app.core.config import settings
from app.models.file import UploadedFile


async def _save_uploaded_file_without_subdirs(db, user, upload):
    root = Path(settings.local_storage_path)
    original_filename = upload.filename or "upload.bin"
    suffix = Path(original_filename).suffix.lower()
    extension = suffix.lstrip(".") or None
    generated_name = f"{uuid.uuid4().hex}{suffix}"
    storage_path = root / generated_name

    checksum = hashlib.sha256()
    size_bytes = 0
    with storage_path.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            checksum.update(chunk)
            size_bytes += len(chunk)
            output.write(chunk)
    await upload.close()

    file_record = UploadedFile(
        user_id=user.id,
        filename=generated_name,
        original_filename=original_filename,
        mime_type=upload.content_type,
        extension=extension,
        size_bytes=size_bytes,
        storage_path=generated_name,
        checksum=checksum.hexdigest(),
        metadata_json={"content_type": upload.content_type} if upload.content_type else None,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record



def test_desktop_layout_crud_flow(client) -> None:
    create_response = client.post(
        "/api/v1/desktop/layouts",
        json={"name": "workspace", "layout_json": {"widgets": [{"id": "w1"}]}}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    layout_id = created["id"]

    get_response = client.get(f"/api/v1/desktop/layouts/{layout_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "workspace"

    patch_response = client.patch(
        f"/api/v1/desktop/layouts/{layout_id}",
        json={"name": "workspace-v2", "layout_json": {"widgets": [{"id": "w2"}], "theme": "light"}},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "workspace-v2"
    assert patch_response.json()["layout_json"]["theme"] == "light"

    upsert_response = client.put(
        "/api/v1/desktop/layout",
        json={"name": "default", "layout_json": {"items": [1, 2, 3]}},
    )
    assert upsert_response.status_code == 200
    assert upsert_response.json()["name"] == "default"

    latest_response = client.get("/api/v1/desktop/layout", params={"name": "default"})
    assert latest_response.status_code == 200
    assert latest_response.json()["layout_json"]["items"] == [1, 2, 3]

    list_response = client.get("/api/v1/desktop/layouts")
    assert list_response.status_code == 200
    assert {item["name"] for item in list_response.json()} == {"workspace-v2", "default"}

    delete_response = client.delete(f"/api/v1/desktop/layouts/{layout_id}")
    assert delete_response.status_code == 200

    deleted_response = client.get(f"/api/v1/desktop/layouts/{layout_id}")
    assert deleted_response.status_code == 404



def test_file_upload_download_and_delete_flow(client, monkeypatch) -> None:
    monkeypatch.setattr(files_api, "save_uploaded_file", _save_uploaded_file_without_subdirs)

    file_content = b"chapter 1\nlimit definition"

    upload_response = client.post(
        "/api/v1/files/upload",
        files={"upload": ("notes.txt", file_content, "text/plain")},
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    file_id = uploaded["id"]
    assert uploaded["original_filename"] == "notes.txt"
    assert uploaded["mime_type"] == "text/plain"
    assert uploaded["metadata_json"] == {"content_type": "text/plain"}

    list_response = client.get("/api/v1/files")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/v1/files/{file_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["storage_path"].endswith(".txt")

    download_response = client.get(f"/api/v1/files/{file_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == file_content
    assert download_response.headers["content-type"].startswith("text/plain")

    delete_response = client.delete(f"/api/v1/files/{file_id}")
    assert delete_response.status_code == 200

    final_list_response = client.get("/api/v1/files")
    assert final_list_response.status_code == 200
    assert final_list_response.json() == []
