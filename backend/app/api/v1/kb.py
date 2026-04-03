from fastapi import APIRouter


router = APIRouter()


@router.get("/documents")
def list_documents_placeholder() -> dict[str, str]:
    return {"message": "List knowledge documents endpoint placeholder"}


@router.post("/retrieve")
def retrieve_placeholder() -> dict[str, str]:
    return {"message": "Knowledge retrieve endpoint placeholder"}
