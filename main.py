from typing import List, Union

from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field, ValidationError
import httpx
import re
from pangea_client import check_url
from models import Message, WebhookMessage

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")


async def http422_error_handler(
    _: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    toprint = await _.json()
    print(toprint)
    return JSONResponse({"errors": exc.errors()}, status_code=422)


app.add_exception_handler(ValidationError, http422_error_handler)
app.add_exception_handler(RequestValidationError, http422_error_handler)


async def send_message(business_number, message: Message, response_txt: str):
    message_data = {
        "messaging_product": "whatsapp",
        "to": message.from_user,
        "text": {"body": response_txt},
        "context": {"message_id": message.id},
    }
    url = f"https://graph.facebook.com/v18.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


def extract_urls(text):
    # Regular expression pattern to match URLs
    url_pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)

    # Extract the first element of each tuple in the list of URLs
    urls = [url[0] for url in urls]

    return urls


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
        if webhook_changes[0].value.messages:
            if message.entry[0].changes[0].value.messages[0].type == "text":
                business_number = webhook_changes[0].value.metadata.phone_number_id
                urls = extract_urls(webhook_changes[0].value.messages[0].text.body)
                print(urls)
                for url in urls:
                    verdict, score = check_url(url)
                    if int(score) > 80:
                        await send_message(
                            business_number,
                            webhook_changes[0].value.messages[0],
                            f"This url: {url} is malicious",
                        )
                    print(verdict, score)

        for change in webhook_changes:
            print(change.value.metadata.display_phone_number)

    # await send_reply_message(business_phone_number_id, messages[0])

    return Response(status_code=200)
