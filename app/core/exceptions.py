class AppError(Exception):
    """Base class for errors we raise on purpose."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class BadRequestError(AppError):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(400, detail)


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(401, detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Not found"):
        super().__init__(404, detail)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(409, detail)
