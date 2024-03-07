# mypy: ignore-errors

"""An ABSTRACT DATA MODEL, Singleton, to represent a class that should only have one instance."""  # noqa: W505

from typing import ClassVar, Generic, TypeVar

T = TypeVar("T")


class SingletonMeta(type, Generic[T]):
    """
    SingletonMeta is a metaclass that creates a Singleton instance of a class.

    Singleton design pattern restricts the instantiation of a class to a single
    instance. This is useful when exactly one object is needed to coordinate
    actions across the system.
    """

    _instances: ClassVar[dict[T, T]] = {}  # type: ignore  # noqa: PGH003

    def __call__(cls, *args, **kwargs) -> T:
        """
        Override the __call__ method.

        If the class exists, otherwise creates a new instance and stores it in
        the _instances dictionary.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance  # type: ignore  # noqa: PGH003

        return cls._instances[cls]  # type: ignore  # noqa: PGH003
