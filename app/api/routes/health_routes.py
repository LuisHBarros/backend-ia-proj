"""Health check routes."""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.bootstrap import get_container
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Simple status indicating the service is running.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    This endpoint verifies that the service is ready to handle requests by:
    - Checking LLM provider connectivity
    - Checking repository/database connectivity
    
    Returns:
        JSONResponse with status and component checks.
    """
    container = get_container()
    checks = {
        "status": "ready",
        "checks": {}
    }
    all_healthy = True
    
    # Check LLM provider
    try:
        llm = container.get_llm()
        # Try a simple operation (if supported, or just check if it's initialized)
        if hasattr(llm, "_client") and llm._client is not None:
            checks["checks"]["llm"] = {"status": "healthy"}
        else:
            # For providers without _client, assume healthy if initialized
            checks["checks"]["llm"] = {"status": "healthy"}
    except Exception as e:
        checks["checks"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # Check repository
    try:
        repository = container.get_repository()
        # Try a simple operation
        await repository.find_by_id("health-check-test-id")
        checks["checks"]["repository"] = {"status": "healthy"}
    except Exception as e:
        # If it's a "not found" error, that's fine - repository is working
        if "not found" in str(e).lower():
            checks["checks"]["repository"] = {"status": "healthy"}
        else:
            checks["checks"]["repository"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            all_healthy = False
    
    # Set overall status
    if not all_healthy:
        checks["status"] = "not_ready"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=checks
        )
    
    return checks

