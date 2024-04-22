from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime, timedelta


class Text(BaseModel):
    body: str


class Image(BaseModel):
    mime_type: str
    sha256: str
    id: str


class Message(BaseModel):
    from_user: str = Field(..., alias="from", alternate=True)
    id: str
    timestamp: str
    type: str
    text: Optional[Text]
    image: Optional[Image]


class Profile(BaseModel):
    name: str


class Contact(BaseModel):
    wa_id: str
    profile: Profile


class ErrorData(BaseModel):
    messaging_product: str
    details: str


class WhatsappError(BaseModel):
    code: int
    details: str
    fbtrace_id: str
    message: str
    error_data: ErrorData
    error_subcode: int
    type: str


class MetaData(BaseModel):
    display_phone_number: str
    phone_number_id: str


class Origin(BaseModel):
    type: str


class Conversation(BaseModel):
    id: str
    expiration_timestamp: Optional[str]
    origin: Origin


class Pricing(BaseModel):
    pricing_model: str
    billable: bool
    category: str


class Status(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str
    conversation: Optional[Conversation]
    pricing: Optional[Pricing]
    errors: Optional[WhatsappError]


class Value(BaseModel):
    messaging_product: str
    metadata: MetaData
    messages: Optional[List[Message]]
    contacts: Optional[List[Contact]]
    errors: Optional[List[WhatsappError]]
    statuses: Optional[List[Status]]


class Change(BaseModel):
    value: Value
    field: str


class Entry(BaseModel):
    id: str
    changes: List[Change]


class WebhookMessage(BaseModel):
    entry: List[Entry]
