from fastapi import APIRouter


router = APIRouter()


@router.post("/generate")
def generate_practice_placeholder() -> dict[str, str]:
    return {"message": "Generate practice endpoint placeholder"}


@router.get("/sets")
def list_practice_sets_placeholder() -> dict[str, str]:
    return {"message": "List practice sets endpoint placeholder"}
