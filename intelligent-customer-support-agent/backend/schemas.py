from pydantic import BaseModel, EmailStr, Field


class TicketCreate(BaseModel):
    subject: str = Field(min_length=4, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    customer_email: str = Field(min_length=5, max_length=254)


class TicketStatusUpdate(BaseModel):
    status: str = Field(pattern="^(Open|In Review|Resolved)$")
