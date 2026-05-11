from datetime import UTC, datetime

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "xueta-backend",
        "timestamp": datetime.now(UTC).isoformat(),
    }
