import logging
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

class HealthService:
    @staticmethod
    def check_health(config):
        """
        Executes diagnostic probes verifying database connection and service vitality.
        """
        db_status = "unhealthy"
        try:
            db.session.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health probe failed: {e}")
            db_status = f"unhealthy: {str(e)}"

        return {
            "service": "JOURNEX Backend REST API",
            "status": "operational",
            "version": "1.0.0",
            "api_version": config.get("API_VERSION", "v1"),
            "environment": config.get("ENV", "development"),
            "database": {
                "engine": db.engine.name if db.engine else "unknown",
                "status": db_status
            }
        }
