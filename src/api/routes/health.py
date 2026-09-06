from fastapi import APIRouter, Depends

from api.deps import settings_dep
from core.config import Settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "ai-customer-support-platform",
    }


@router.get("/config")
def client_config(settings: Settings = Depends(settings_dep)) -> dict[str, object]:
    """Non-secret settings the web UI needs to render itself."""
    return {
        "llm_configured": settings.llm_configured,
        "model": settings.model,
        "max_agent_steps": settings.max_agent_steps,
    }
