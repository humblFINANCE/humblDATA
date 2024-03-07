"""An ABSTRACT DATA MODEL, CustomError, to be inherited by other models."""



class CustomError(BaseException):
    """Wrong Arguments Error."""

    def __init__(self, original: str | Exception | None = None):
        self.original = original
        super().__init__(str(original))
