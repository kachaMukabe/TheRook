from typing import TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class RapidProCallback(BaseModel):
    id: str
    to: str
    to_no_plus: str
    from_: str = Field(alias="from")
    from_no_plus: str
    channel: str
    text: str


class RapidContact(BaseModel):
    uuid: str
    urn: str
    name: str


class RapidFlow(BaseModel):
    uuid: str
    name: str


class RapidResults(BaseModel):
    value: str
    category: str


class RapidProEmailMessage(BaseModel):
    contact: RapidContact
    flow: RapidFlow
    results: T
