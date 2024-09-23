from typing import Union
import urllib.parse
import json

from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from dotenv import load_dotenv
from pydantic import ValidationError
from models import WebhookMessage
from message_handler import handle_whatsapp_message, send_rapid_message

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")


async def http422_error_handler(
    _: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    toprint = await _.json()
    print("Start request")
    print(toprint)
    print("End request")
    return JSONResponse({"errors": exc.errors()}, status_code=422)


app.add_exception_handler(ValidationError, http422_error_handler)
app.add_exception_handler(RequestValidationError, http422_error_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Print request method and URL
    print(f"Incoming request: {request.method} {request.url}")

    # Optionally, print headers or body
    headers = dict(request.headers)
    print(f"Headers: {headers}")

    body = await request.body()
    print(f"Body: {body.decode('utf-8') if body else 'No body'}")

    # Proceed with the request
    response = await call_next(request)
    return response


@app.get("/")
def index():
    return {"response": "Hello World"}


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
    await handle_whatsapp_message(message)

    return Response(status_code=200)


@app.post("/callback")
async def rapid_pro_callback(request: Request):
    print("working")
    body = await request.body()
    decoded_data = body.decode("utf-8")
    parsed_data = urllib.parse.parse_qs(decoded_data)
    cleaned_data = {key: value[0].strip('"') for key, value in parsed_data.items()}

    # Convert the dictionary to a JSON string
    json_data = json.dumps(cleaned_data, indent=4)
    print(json_data)
    await send_rapid_message(cleaned_data["to"], cleaned_data["text"])
    return Response("success", status_code=200)
