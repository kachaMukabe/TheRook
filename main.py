from typing import Union
import urllib.parse
import json
import yaml
import logging
from pydantic_core import from_json
import uvicorn

from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import sys
from dotenv import load_dotenv
from pydantic import ValidationError
from models import WebhookMessage, Section, Row
from message_handler import (
    handle_whatsapp_message,
    send_location_request_message,
    send_rapid_message,
    send_interactive_list,
    send_image_message,
    send_catalog_message,
)

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

logging_config = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)


async def http422_error_handler(
    _: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    print("Start request")
    toprint = await _.json()
    print(toprint)
    print("End request")
    logger.error(toprint)
    return JSONResponse({"errors": exc.errors()}, status_code=422)


app.add_exception_handler(ValidationError, http422_error_handler)
app.add_exception_handler(RequestValidationError, http422_error_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Print request method and URL
    print(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Incoming request: {request.method} {request.url}")

    # Optionally, print headers or body
    headers = dict(request.headers)
    print(f"Headers: {headers}")

    body = await request.body()
    print(f"Body: {body.decode('utf-8') if body else 'No body'}")
    logger.info(f"Body: {body.decode('utf-8') if body else 'No body'}")

    # Proceed with the request
    response = await call_next(request)
    return response


@app.get("/")
def index():
    return {"response": "No longer hello world but another test:Hello World Again"}


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
    logger.info("Incoming webhook message:", message)

    # Check if the webhook request contains a message
    await handle_whatsapp_message(message)

    return Response(status_code=200)


@app.post("/callback")
async def rapid_pro_callback(request: Request):
    print("working")
    logging.info("working")
    body = await request.body()
    decoded_data = body.decode("utf-8")
    parsed_data = urllib.parse.parse_qs(decoded_data)
    cleaned_data = {key: value[0].strip('"') for key, value in parsed_data.items()}

    message_data = yaml.safe_load(cleaned_data["text"])
    logging.info(message_data)

    if type(message_data) is dict:
        if message_data["type"] == "interactive":
            logging.info("In interactive")
            sections = [
                Section.model_validate(section) for section in message_data["sections"]
            ]
            header_text = message_data["header"]
            body_text = message_data["body"]
            footer_text = message_data["footer"]
            button_text = message_data["button"]
            await send_interactive_list(
                cleaned_data["to"],
                message_data["header"],
                message_data["body"],
                message_data["footer"],
                message_data["button"],
                sections,
            )
        elif message_data["type"] == "image":
            caption_text = message_data["caption"]
            media_id = message_data["media_id"]
            await send_image_message(
                cleaned_data["to"], caption=caption_text, media_id=media_id
            )
        elif message_data["type"] == "catalog":
            body_text = message_data["body"]
            footer_text = message_data["footer"]
            catalog_id = message_data["catalog"]
            product_id = message_data["product"]
            await send_catalog_message(
                cleaned_data["to"], body_text, footer_text, catalog_id, product_id
            )
        elif message_data["type"] == "location":
            await send_location_request_message(
                cleaned_data["to"], message_data["body"]
            )
    else:
        await send_rapid_message(cleaned_data["to"], message_data)
    return Response("success", status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
