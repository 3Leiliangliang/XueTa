from fastapi import APIRouter


router = APIRouter()


@router.post("/upload")
def upload_placeholder() -> dict[str, str]:
    return {"message": "File upload endpoint placeholder"}
