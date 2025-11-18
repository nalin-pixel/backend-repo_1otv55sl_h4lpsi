"""
Database Schemas for Jamie Andrew Car Services (Doha, Qatar)

Each Pydantic model below represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class Customer(BaseModel):
    """
    customers collection
    Collection name: "customer"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="WhatsApp / phone number")
    city: str = Field("Doha", description="City")
    country: str = Field("Qatar", description="Country")

    car_make: str = Field(..., description="Car make, e.g., Toyota")
    car_model: str = Field(..., description="Car model, e.g., Camry")
    car_year: Optional[int] = Field(None, ge=1970, le=2100, description="Car year")
    plate_number: Optional[str] = Field(None, description="License plate number")


class Plan(BaseModel):
    """
    plans collection
    Collection name: "plan"
    """
    name: str = Field(..., description="Plan name")
    tier: str = Field(..., description="Tier identifier, e.g., basic, standard, premium")
    price_qr: float = Field(..., ge=0, description="Monthly price in QAR")
    description: Optional[str] = Field(None, description="Short description")
    features: List[str] = Field(default_factory=list, description="List of plan features")
    is_active: bool = Field(True, description="Whether plan is active")


class Subscription(BaseModel):
    """
    subscriptions collection
    Collection name: "subscription"
    """
    customer_id: str = Field(..., description="Customer document id")
    plan_id: str = Field(..., description="Plan document id")
    status: str = Field("active", description="active | paused | canceled")
    starts_at: Optional[datetime] = Field(None, description="Start date")
    renews_at: Optional[datetime] = Field(None, description="Next renewal date")


class Booking(BaseModel):
    """
    bookings collection
    Collection name: "booking"
    """
    subscription_id: str = Field(..., description="Subscription document id")
    service_type: str = Field(..., description="Requested service type, e.g., wash, detailing, oil-change")
    scheduled_date: datetime = Field(..., description="Scheduled date/time (UTC)")
    location: str = Field(..., description="Service location / address")
    notes: Optional[str] = Field(None, description="Additional notes")
    status: str = Field("scheduled", description="scheduled | in-progress | completed | canceled")


# These schemas are auto-read by the database viewer tool.
