from datetime import datetime, timezone
from flask import jsonify

def api_response(data=None, message="Success", status_code=200, success=True, errors=None):
    """
    Standardized JSON Response Envelope for all JOURNEX API endpoints.
    """
    payload = {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return jsonify(payload), status_code
