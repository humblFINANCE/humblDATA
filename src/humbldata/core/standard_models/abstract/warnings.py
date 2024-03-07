from warnings import WarningMessage

from pydantic import BaseModel


class Warning_(BaseModel):  # noqa: N801, D101
    category: str
    message: str


def cast_warning(w: WarningMessage) -> Warning_:  # noqa: D103
    return Warning_(
        category=w.category.__name__,
        message=str(w.message),
    )


class HumblDataWarning(Warning):  # noqa: D101
    pass
