import logging
from flask_limiter.errors import RateLimitExceeded
from app.utils.response import api_response
from app.utils.exceptions import APIException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Centralized error handlers registering clean JSON envelopes for client consumption.
    """

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        return api_response(
            data=error.payload,
            message=error.message,
            status_code=error.status_code,
            success=False,
            errors={"code": error.status_code, "type": error.__class__.__name__}
        )

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(error):
        return api_response(
            message=f"Rate limit exceeded: {error.description}",
            status_code=429,
            success=False,
            errors={"code": 429, "type": "RateLimitExceeded", "description": str(error.description)}
        )

    @app.errorhandler(400)
    def bad_request(error):
        return api_response(
            message="Bad Request: The request could not be understood or is missing required parameters.",
            status_code=400,
            success=False,
            errors={"code": 400, "description": str(error.description)}
        )

    @app.errorhandler(404)
    def not_found(error):
        return api_response(
            message="Resource Not Found: The requested endpoint does not exist.",
            status_code=404,
            success=False,
            errors={"code": 404, "description": str(error.description)}
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return api_response(
            message="Method Not Allowed: The HTTP method is not supported for this endpoint.",
            status_code=405,
            success=False,
            errors={"code": 405, "description": str(error.description)}
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error("Internal Server Error: %s", error, exc_info=True)
        return api_response(
            message="Internal Server Error: An unexpected error occurred on the server.",
            status_code=500,
            success=False,
            errors={"code": 500, "type": "InternalServerError"}
        )
