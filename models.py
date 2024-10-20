from optparse import Option

from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime, timedelta


class Text(BaseModel):
    body: str


class Image(BaseModel):
    mime_type: str
    sha256: str
    id: str


class ListReply(BaseModel):
    id: str
    title: str
    description: str


class Interactive(BaseModel):
    type: str
    list_reply: Optional[ListReply] = Field(None, description="List reply")


class Location(BaseModel):
    latitude: str
    longitude: str
    name: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    url: Optional[str] = Field(None)


class Message(BaseModel):
    from_user: str = Field(..., alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[Text] = Field(None, description="Message text")
    image: Optional[Image] = Field(None, description="Message image")
    interactive: Optional[Interactive] = Field(None, description="Interactive object")
    location: Optional[Location] = Field(None, description="Location object")


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
    expiration_timestamp: Optional[str] = Field(
        None, description="Expiration timestamp"
    )
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
    conversation: Optional[Conversation] = Field(None, description="Conversation")
    pricing: Optional[Pricing] = Field(None, description="Pricing")
    errors: Optional[WhatsappError] = Field(None, description="Errors")


class Value(BaseModel):
    messaging_product: str
    metadata: MetaData
    messages: Optional[List[Message]] = Field(None, description="List of messages")
    contacts: Optional[List[Contact]] = Field(None, description="List of contacts")
    errors: Optional[List[WhatsappError]] = Field(None, description="List of errors")
    statuses: Optional[List[Status]] = Field(None, description="List of statuses")


class Change(BaseModel):
    value: Value
    field: str


class Entry(BaseModel):
    id: str
    changes: List[Change]


class WebhookMessage(BaseModel):
    object: str
    entry: List[Entry]


class RapidProMessage(BaseModel):
    id: str
    to: str
    to_no_plus: str
    from_: str = Field(alias="from")
    from_no_plus: str
    channel: str
    text: str


### WHATSAPP MESSAGE SENDING MODELS
class Row(BaseModel):
    id: str
    title: str
    description: str


class Section(BaseModel):
    title: str
    rows: List[Row]
