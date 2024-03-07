"""An ABSTRACT DATA MODEL to be inherited by custom errors."""


class HumblDataError(BaseException):
    """Base Error for HumblData logic."""

    def __init__(self, original: str | Exception | None = None):
        self.original = original
        super().__init__(str(original))
