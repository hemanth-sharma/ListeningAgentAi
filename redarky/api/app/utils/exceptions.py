class DomainException(Exception):
    """Base exception for all domain-specific errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundException(DomainException):
    """Raised when a requested database record does not exist."""
    pass

class UnauthorizedException(DomainException):
    """Raised when a user attempts to access a resource they don't own."""
    pass

# Specific Entity Definitions
class ProjectNotFound(NotFoundException):
    def __init__(self, project_id: str):
        super().__init__(f"Project with ID '{project_id}' was not found or access is denied.")

class LeadNotFound(NotFoundException):
    def __init__(self, lead_id: str):
        super().__init__(f"Lead with ID '{lead_id}' was not found.")