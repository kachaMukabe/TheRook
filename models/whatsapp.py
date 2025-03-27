from typing import List, Optional
from pydantic import BaseModel


class Row(BaseModel):
    id: str
    title: str
    description: str


class Section(BaseModel):
    title: str
    rows: List[Row]


### TEMPLATE MODELS
class Language(BaseModel):
    code: str


class ProductItem(BaseModel):
    product_retailer_id: str


class ProductSection(BaseModel):
    title: str
    product_items: List[ProductItem]


class Action(BaseModel):
    thumbnail_product_retailer_id: str
    sections: List[ProductSection]


class Parameter(BaseModel):
    type: str
    text: Optional[str] = None
    action: Optional[Action] = None


class Component(BaseModel):
    type: str
    parameters: List[Parameter]
    sub_type: Optional[str] = None
    index: Optional[int] = None


class Template(BaseModel):
    name: str
    language: Language
    components: List[Component]


class Model(BaseModel):
    messaging_product: str
    recipient_type: str
    to: str
    type: str
    template: Template
