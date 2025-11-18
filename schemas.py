"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (you can keep these alongside your own)

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# NovaCall core schemas

class CallTask(BaseModel):
    """
    Outbound call task created for NovaCall to execute
    Collection: "calltask"
    """
    target_phone: str = Field(..., description="E.164 formatted target phone number")
    intent: str = Field(..., description="Purpose of the call in one sentence")
    script: Optional[str] = Field(None, description="Full conversation script if provided")
    talking_points: Optional[List[str]] = Field(None, description="Key talking points to cover")
    fallback_conditions: Optional[List[str]] = Field(None, description="Triggers for escalation/transfer")
    voice_model_id: str = Field(..., description="Pre-trained voice model ID for Manohar's voice")
    consent_required: bool = Field(False, description="Whether to play a recording disclaimer")
    status: str = Field("pending", description="Call status: pending|in_progress|completed|failed|transferred")

class TranscriptLog(BaseModel):
    """
    Per-utterance transcript log for a given call
    Collection: "transcriptlog"
    """
    call_id: str = Field(..., description="Associated call task ID")
    role: str = Field(..., description="speaker role: assistant|callee|system")
    text: str = Field(..., description="transcribed content or system note")
    timestamp: Optional[datetime] = Field(default=None, description="UTC timestamp of the utterance")
    outcome: Optional[str] = Field(default=None, description="Final outcome if this entry ends the call")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
