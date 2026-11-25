from flask import Blueprint, current_app
from app.services.health_service import HealthService
from app.utils.response import api_response

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint verifying backend and database vitality.
    Route: GET /api/v1/health
    """
    health_data = HealthService.check_health(current_app.config)
    is_healthy = health_data["database"]["status"] == "healthy"
    status_code = 200 if is_healthy else 503

    return api_response(
        data=health_data,
        message="JOURNEX Backend is operational." if is_healthy else "Service Degraded.",
        status_code=status_code,
        success=is_healthy
    )
