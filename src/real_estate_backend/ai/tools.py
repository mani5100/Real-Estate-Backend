from typing import Literal, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from real_estate_backend.leads.model import Lead, LeadStatus
from real_estate_backend.customers.model import Customer
from real_estate_backend.core.event_bus import event_bus
from real_estate_backend.core.events import LeadStatusChangedEvent
from real_estate_backend.core.logging import logger


# ── Tool Argument Schemas ────────────────────────────────────────────────────
# Pydantic models for each tool's input arguments.
# The dispatcher validates args through these before hitting the DB.

class GetNewLeadsArgs(BaseModel):
    pass


class GetLeadDetailArgs(BaseModel):
    lead_id: int


class QualifyLeadArgs(BaseModel):
    lead_id: int


# ── Tool Result Schemas ──────────────────────────────────────────────────────
# Pydantic models for what each tool returns.
# The model receives these as structured context, not raw DB objects.

class LeadSummary(BaseModel):
    id: int
    customer_name: str
    property_title: str
    property_city: str
    property_type: str | None


class GetNewLeadsResult(BaseModel):
    count: int
    leads: list[LeadSummary]


class CustomerInfo(BaseModel):
    name: str
    email: str
    phone: str | None


class PropertyInfo(BaseModel):
    title: str
    city: str
    address: str
    type: str | None
    bedrooms: int
    asking_price: int


class CustomerIntent(BaseModel):
    budget: int | None
    payment_method: str | None
    notes: str | None


class GetLeadDetailResult(BaseModel):
    lead_id: int
    status: str
    customer: CustomerInfo
    property: PropertyInfo
    customer_intent: CustomerIntent


class QualifyLeadResult(BaseModel):
    success: bool
    lead_id: int
    old_status: str
    new_status: str


class ToolErrorResult(BaseModel):
    success: Literal[False] = False
    error: str


# ── Tool Definition Schema ───────────────────────────────────────────────────
# What gets shown to the model in the system prompt.

class ToolArgDefinition(BaseModel):
    name: str
    type: str
    description: str
    required: bool


class ToolDefinition(BaseModel):
    name: str
    description: str
    args: list[ToolArgDefinition]


# ── Tool Registry ────────────────────────────────────────────────────────────
# Single source of truth for all tool definitions.
# The system prompt is built from this — no duplication.

TOOL_REGISTRY: list[ToolDefinition] = [
    ToolDefinition(
        name="get_new_leads",
        description="Fetches all NEW leads assigned to the current agent. Call this on greeting or when agent asks to see their leads.",
        args=[],
    ),
    ToolDefinition(
        name="get_lead_detail",
        description="Fetches full detail of a single lead including customer info, property details, budget, payment method and notes.",
        args=[
            ToolArgDefinition(
                name="lead_id",
                type="integer",
                description="The id of the lead to fetch",
                required=True,
            )
        ],
    ),
    ToolDefinition(
        name="qualify_lead",
        description="Changes a lead status from NEW to QUALIFIED. Call this only when agent explicitly confirms they want to qualify.",
        args=[
            ToolArgDefinition(
                name="lead_id",
                type="integer",
                description="The id of the lead to qualify",
                required=True,
            )
        ],
    ),
]


# ── Tool Executors ───────────────────────────────────────────────────────────

def _execute_get_new_leads(
    db: Session,
    agent_user_id: int,
) -> GetNewLeadsResult | ToolErrorResult:
    try:
        leads = list(
            db.scalars(
                select(Lead)
                .options(
                    joinedload(Lead.property),
                    joinedload(Lead.customer).joinedload(Customer.user),
                )
                .where(
                    Lead.agent_id == agent_user_id,
                    Lead.status == LeadStatus.NEW,
                )
                .order_by(Lead.id.asc())
            ).all()
        )

        return GetNewLeadsResult(
            count=len(leads),
            leads=[
                LeadSummary(
                    id=lead.id,
                    customer_name=lead.customer.user.full_name,
                    property_title=lead.property.title,
                    property_city=lead.property.city,
                    property_type=(
                        lead.property.property_type.value
                        if lead.property.property_type
                        else None
                    ),
                )
                for lead in leads
            ],
        )

    except Exception as e:
        logger.error("get_new_leads failed", extra={"error": str(e)})
        return ToolErrorResult(error=str(e))


def _execute_get_lead_detail(
    db: Session,
    lead_id: int,
    agent_user_id: int,
) -> GetLeadDetailResult | ToolErrorResult:
    try:
        lead = db.scalar(
            select(Lead)
            .options(
                joinedload(Lead.property),
                joinedload(Lead.customer).joinedload(Customer.user),
            )
            .where(
                Lead.id == lead_id,
                Lead.agent_id == agent_user_id,
            )
        )

        if not lead:
            return ToolErrorResult(
                error=f"Lead {lead_id} not found or not assigned to you"
            )

        return GetLeadDetailResult(
            lead_id=lead.id,
            status=lead.status.value,
            customer=CustomerInfo(
                name=lead.customer.user.full_name,
                email=lead.customer.user.email,
                phone=lead.customer.phone,
            ),
            property=PropertyInfo(
                title=lead.property.title,
                city=lead.property.city,
                address=lead.property.address,
                type=(
                    lead.property.property_type.value
                    if lead.property.property_type
                    else None
                ),
                bedrooms=lead.property.bedrooms,
                asking_price=lead.property.price,
            ),
            customer_intent=CustomerIntent(
                budget=lead.budget,
                payment_method=(
                    lead.payment_method.value
                    if lead.payment_method
                    else None
                ),
                notes=lead.notes,
            ),
        )

    except Exception as e:
        logger.error("get_lead_detail failed", extra={"error": str(e)})
        return ToolErrorResult(error=str(e))


def _execute_qualify_lead(
    db: Session,
    lead_id: int,
    agent_user_id: int,
) -> QualifyLeadResult | ToolErrorResult:
    try:
        lead = db.scalar(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.agent_id == agent_user_id,
            )
        )

        if not lead:
            return ToolErrorResult(
                error=f"Lead {lead_id} not found or not assigned to you"
            )

        if lead.status != LeadStatus.NEW:
            return ToolErrorResult(
                error=f"Lead {lead_id} is {lead.status.value}. Only NEW leads can be qualified"
            )

        old_status = lead.status
        lead.status = LeadStatus.QUALIFIED

        db.commit()
        db.refresh(lead)

        event_bus.emit(
            "lead.status.changed",
            LeadStatusChangedEvent(
                lead_id=lead.id,
                customer_id=lead.customer_id,
                property_id=lead.property_id,
                old_status=old_status,
                new_status=lead.status,
                agent_id=lead.agent_id,
            ),
        )

        logger.info("Lead qualified via chatbot", extra={
            "lead_id": lead.id,
            "agent_id": agent_user_id,
        })

        return QualifyLeadResult(
            success=True,
            lead_id=lead.id,
            old_status=old_status.value,
            new_status=lead.status.value,
        )

    except Exception as e:
        db.rollback()
        logger.error("qualify_lead failed", extra={"error": str(e)})
        return ToolErrorResult(error=str(e))


# ── Tool Dispatcher ──────────────────────────────────────────────────────────
# Single entry point for the agentic loop.
# Validates args via Pydantic before executing.
# Always returns a Pydantic model — never raw dicts.

def execute_tool(
    tool_name: str,
    args: dict,
    db: Session,
    agent_user_id: int,
) -> GetNewLeadsResult | GetLeadDetailResult | QualifyLeadResult | ToolErrorResult:

    logger.info("Tool called", extra={
    "tool": tool_name,
    "tool_args": args,
    "agent_id": agent_user_id,
})

    if tool_name == "get_new_leads":
        GetNewLeadsArgs(**args)
        return _execute_get_new_leads(db=db, agent_user_id=agent_user_id)

    if tool_name == "get_lead_detail":
        validated = GetLeadDetailArgs(**args)
        return _execute_get_lead_detail(
            db=db,
            lead_id=validated.lead_id,
            agent_user_id=agent_user_id,
        )

    if tool_name == "qualify_lead":
        validated = QualifyLeadArgs(**args)
        return _execute_qualify_lead(
            db=db,
            lead_id=validated.lead_id,
            agent_user_id=agent_user_id,
        )

    return ToolErrorResult(error=f"Unknown tool: {tool_name}")