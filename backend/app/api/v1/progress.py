from fastapi import APIRouter


router = APIRouter()


@router.get("/overview")
def progress_overview_placeholder() -> dict[str, str]:
    return {"message": "Progress overview endpoint placeholder"}


@router.get("/mastery")
def mastery_placeholder() -> dict[str, str]:
    return {"message": "Knowledge mastery endpoint placeholder"}
