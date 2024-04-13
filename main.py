from typing import List, Union

from fastapi import FastAPI, Query, Response
import os
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
import httpx

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")


class Text(BaseModel):
    body: str


class Message(BaseModel):
    from_user: str = Field(..., alias="from", alternate=True)
    id: str
    timestamp: str
    type: str
    text: Text


class MetaData(BaseModel):
    display_phone_number: str
    phone_number_id: str


class Value(BaseModel):
    messaging_product: str
    metadata: MetaData
    messages: List[Message]


class Change(BaseModel):
    value: Value
    field: str


class Entry(BaseModel):
    id: str
    changes: List[Change]


class WebhookMessage(BaseModel):
    entry: List[Entry]


async def send_message(business_number, message: Message):
    message_data = {
        "messaging_product": "whatsapp",
        "to": message.from_user,
        "text": {"body": "Echo: " + message.text.body},
        "context": {"message_id": message.id},
    }
    url = f"https://graph.facebook.com/v18.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


@app.get("/webhook")
def webhook(
    mode: Union[str, None] = Query(default=None, alias="hub.mode"),
    token: Union[str, None] = Query(default=None, alias="hub.verify_token"),
    challenge: Union[str, None] = Query(default=None, alias="hub.challenge"),
):
    print(mode, token, challenge)
    print(VERIFY_TOKEN)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Working here?", challenge)
        return Response(challenge, status_code=200)
    return Response(status_code=403)


@app.post("/webhook")
async def receive_message(message: WebhookMessage):
    print("Incoming webhook message:", message)

    # Check if the webhook request contains a message
    if message.entry and message.entry[0].changes:
        webhook_changes = message.entry[0].changes
        # Loop through changes to find a message
        if message.entry[0].changes[0].value.messages[0].type == "text":
            business_number = webhook_changes[0].value.metadata.phone_number_id
            await send_message(business_number, webhook_changes[0].value.messages[0])

        for change in webhook_changes:
            print(change.value.metadata.display_phone_number)

    # await send_reply_message(business_phone_number_id, messages[0])

    return Response(status_code=200)
