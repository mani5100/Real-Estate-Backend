import enum


class UserRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"
    
class AgentApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    
class PropertyType(str, enum.Enum):
    ROOM = "room"
    APARTMENT = "apartment"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHEQUE = "cheque"