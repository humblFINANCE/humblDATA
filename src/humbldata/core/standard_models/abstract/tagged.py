"""An ABSTRACT DATA MODEL, Tagged, to be inherited by other models as identifier."""  # noqa: W505

from pydantic import BaseModel, Field
from uuid_extensions import uuid7str


class Tagged(BaseModel):
    """A class to represent an object tagged with a uuid7."""

    id: str = Field(default_factory=uuid7str, alias="_id")
