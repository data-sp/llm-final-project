from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=self.headers,
        )


class UserAlreadyExistsError(BaseHTTPException):
    status_code = status.HTTP_409_CONFLICT
    detail = "User with this email already exists"


class InvalidCredentialsError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password"
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidTokenError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token"
    headers = {"WWW-Authenticate": "Bearer"}


class TokenExpiredError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token has expired"
    headers = {"WWW-Authenticate": "Bearer"}


class UserNotFoundError(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"


class PermissionDeniedError(BaseHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
