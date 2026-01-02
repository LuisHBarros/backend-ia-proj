"""Domain exceptions."""


class DomainException(Exception):
    """Base exception for domain layer."""
    pass


class InvalidMessageError(DomainException):
    """Raised when a message is invalid."""
    pass


class LLMError(DomainException):
    """Raised when LLM operation fails."""
    pass


class RepositoryError(DomainException):
    """Raised when repository operation fails."""
    pass

