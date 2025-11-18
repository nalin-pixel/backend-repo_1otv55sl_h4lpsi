import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="Jamie Andrew Car Services - Subscriptions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Jamie Andrew Car Services", "location": "Doha, Qatar", "status": "ok"}


@app.get("/test")
def test_database():
    info = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "collections": [],
    }
    try:
        if db is not None:
            info["database"] = "✅ Connected"
            info["database_url"] = "✅ Set"
            info["database_name"] = getattr(db, "name", "unknown")
            info["collections"] = db.list_collection_names()[:10]
        else:
            info["database"] = "❌ Not Connected"
    except Exception as e:
        info["database"] = f"⚠️ Error: {str(e)[:80]}"
    return info


# ---------- Models for request bodies ----------
class CreateCustomer(BaseModel):
    name: str
    email: str
    phone: str
    car_make: str
    car_model: str
    car_year: Optional[int] = None
    plate_number: Optional[str] = None


class CreatePlan(BaseModel):
    name: str
    tier: str
    price_qr: float
    description: Optional[str] = None
    features: Optional[List[str]] = None


class CreateSubscription(BaseModel):
    customer_id: str
    plan_id: str


class CreateBooking(BaseModel):
    subscription_id: str
    service_type: str
    scheduled_date: datetime
    location: str
    notes: Optional[str] = None


# ---------- Seed endpoint to create starter plans ----------
@app.post("/api/seed")
def seed_plans():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    plans = [
        {
            "name": "Essential Wash",
            "tier": "basic",
            "price_qr": 79.0,
            "description": "Exterior wash + interior vacuum (1x/week)",
            "features": ["Exterior wash", "Interior vacuum", "Tyre shine"],
            "is_active": True,
        },
        {
            "name": "Care Plus",
            "tier": "standard",
            "price_qr": 149.0,
            "description": "Wash + interior detail (2x/month)",
            "features": ["Exterior wash", "Interior detail", "Glass cleaning"],
            "is_active": True,
        },
        {
            "name": "Premium Detail",
            "tier": "premium",
            "price_qr": 299.0,
            "description": "Full detailing + priority booking",
            "features": ["Full detailing", "Wax coat", "Priority booking"],
            "is_active": True,
        },
        {
            "name": "Annual Care",
            "tier": "yearly",
            "price_qr": 1000.0,
            "description": "Yearly subscription with discounted bundled services",
            "features": [
                "Up to 12 washes per year",
                "Quarterly interior detailing",
                "Priority booking",
                "Annual wax and polish",
            ],
            "is_active": True,
        },
    ]

    inserted = 0
    for p in plans:
        existing = db["plan"].find_one({"tier": p["tier"]})
        if not existing:
            db["plan"].insert_one({**p, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)})
            inserted += 1
    return {"inserted": inserted}


# ---------- Public endpoints ----------
@app.get("/api/plans")
def list_plans():
    docs = get_documents("plan", {"is_active": True})
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify for JSON
    return docs


@app.post("/api/customers")
def create_customer(payload: CreateCustomer):
    new_id = create_document("customer", payload.model_dump())
    return {"id": new_id}


@app.post("/api/subscriptions")
def create_subscription(payload: CreateSubscription):
    # Verify references exist
    cust = db["customer"].find_one({"_id": __import__("bson").ObjectId(payload.customer_id)}) if payload.customer_id else None
    plan = db["plan"].find_one({"_id": __import__("bson").ObjectId(payload.plan_id)}) if payload.plan_id else None
    if not cust or not plan:
        raise HTTPException(status_code=404, detail="Customer or Plan not found")

    now = datetime.now(timezone.utc)
    renew = now + timedelta(days=30)
    sub = {
        "customer_id": payload.customer_id,
        "plan_id": payload.plan_id,
        "status": "active",
        "starts_at": now,
        "renews_at": renew,
    }
    sub_id = create_document("subscription", sub)
    return {"id": sub_id}


@app.get("/api/subscriptions")
def list_subscriptions(customer_id: Optional[str] = None):
    query = {"customer_id": customer_id} if customer_id else {}
    items = get_documents("subscription", query)
    for d in items:
        d["_id"] = str(d["_id"])  # stringify
    return items


@app.post("/api/bookings")
def create_booking(payload: CreateBooking):
    # Simple existence check for subscription
    sub = db["subscription"].find_one({"_id": __import__("bson").ObjectId(payload.subscription_id)})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    booking = payload.model_dump()
    booking_id = create_document("booking", booking)
    return {"id": booking_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
