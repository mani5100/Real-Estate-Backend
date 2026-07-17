import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"