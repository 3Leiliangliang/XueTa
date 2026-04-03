from fastapi import APIRouter


router = APIRouter()


@router.get("/layout")
def get_layout_placeholder() -> dict[str, str]:
    return {"message": "Desktop layout endpoint placeholder"}
