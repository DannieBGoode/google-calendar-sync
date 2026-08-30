"""Explicit failures raised by the provider-independent domain."""


class DomainError(Exception):
    """Base class for errors caused by violated business rules."""


class DomainValidationError(DomainError, ValueError):
    """A value cannot represent a valid domain concept."""


class InvalidStateTransition(DomainError):
    """An entity cannot move between the requested lifecycle states."""


class OwnershipNotEstablished(DomainError):
    """A destructive operation was requested without a managed-event mapping."""


class MappingInvariantViolation(DomainError):
    """An event mapping would violate uniqueness or relationship ownership."""
