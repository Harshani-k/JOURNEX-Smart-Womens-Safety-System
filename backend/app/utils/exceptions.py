class APIException(Exception):
    """Base API Exception for structured error propagation."""
    status_code = 500
    message = "An unexpected server error occurred."

    def __init__(self, message=None, status_code=None, payload=None):
        super().__init__()
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        self.payload = payload

class BadRequestException(APIException):
    status_code = 400
    message = "Bad request. Please verify your input parameters."

class UnauthorizedException(APIException):
    status_code = 401
    message = "Unauthorized access. Invalid or missing authentication credentials."

class ForbiddenException(APIException):
    status_code = 403
    message = "Forbidden. You do not have permission to access this resource."

class NotFoundException(APIException):
    status_code = 404
    message = "Resource not found."

class ConflictException(APIException):
    status_code = 409
    message = "Conflict. A resource with these attributes already exists."
