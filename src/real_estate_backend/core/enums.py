import enum


class UserRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"
    
class AgentApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"