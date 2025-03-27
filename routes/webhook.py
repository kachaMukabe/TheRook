from typing import Union
from fastapi import APIRouter, Query, Response

from config import get_store
from message_handler import handle_whatsapp_message
from models.business import Business
from models.webhook import WebhookMessage


router = APIRouter(prefix="/whatsapp", tags=["Webhooks"])


@router.get("/webhook")
def process_register_webhook(
    mode: Union[str, None] = Query(default=None, alias="hub.mode"),
    token: Union[str, None] = Query(default=None, alias="hub.verify_token"),
    challenge: Union[str, None] = Query(default=None, alias="hub.challenge"),
):
    with get_store() as session:
        settings = session.load("webhooks/kabolabs")
        if mode == "subscribe" and token == settings.token:
            return Response(challenge, status_code=200)
    return Response(status_code=403)


@router.post("/webhook")
async def process_messages(message: WebhookMessage):
    if not message.entry:
        return

    if not message.entry[0].changes:
        return

    changes = message.entry[0].changes
    change_field = changes[0].field

    metadata = changes[0].value.metadata
    contacts = changes[0].value.contacts
    messages = changes[0].value.messages
    with get_store() as session:
        user = (
            session.query(object_type=Business)
            .where_equals("business_id", changes[0].value.metadata.phone_number_id)
            .first()
        )
        print(user)
        await handle_whatsapp_message(message, user.rapid_pro_channel)
    return Response(status_code=200)
