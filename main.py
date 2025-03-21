from typing import Union
import yaml
import logging
import uvicorn
import smtplib
import gspread

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Form, Query, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from google.oauth2.service_account import Credentials
import os
import sys
from dotenv import load_dotenv
from pydantic import ValidationError
from models import (
    RapidProEmailMessage,
    RapidProMessage,
    WebhookMessage,
    Section,
    ProductSection,
)
from message_handler import (
    handle_whatsapp_message,
    send_location_request_message,
    send_rapid_message,
    send_interactive_list,
    send_image_message,
    send_catalog_message,
    send_template_message,
)

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
TO_EMAIL_ADDRESS = os.getenv("TO_EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SERVICE_ACCOUNT_FILE = "therook-1a7136b65746.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open Google Sheet by name or ID
SPREADSHEET_ID = "1y2Nw6DifAeT719XO0pqgsiqdlkPPELdSS3JlQu_muH0"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Select the first sheet

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
    logger.info(f"Headers: {headers}")

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
    logger.info(f"Incoming webhook message: {message}")

    # Check if the webhook request contains a message
    await handle_whatsapp_message(message)

    return Response(status_code=200)


@app.post("/callback")
async def rapid_pro_callback(message: RapidProMessage):
    logging.info("working")
    logging.info(message)

    try:
        message_data = yaml.safe_load(message.text)
    except Exception as e:
        logging.error(e)
        message_data = message.text
    logging.info(message_data)

    if type(message_data) is dict:
        if message_data["type"] == "interactive":
            logging.info("In interactive")
            sections = [
                Section.model_validate(section) for section in message_data["sections"]
            ]
            header_text = (
                message_data["header"] if message_data["header"] is not None else ""
            )
            body_text = message_data["body"]
            footer_text = (
                message_data["footer"] if message_data["footer"] is not None else ""
            )
            button_text = message_data["button"]
            await send_interactive_list(
                message.to,
                header_text,
                message_data["body"],
                footer_text,
                message_data["button"],
                sections,
            )
        elif message_data["type"] == "template":
            sections = [
                ProductSection.model_validate(section)
                for section in message_data["sections"]
            ]
            header_text = (
                message_data["header"] if message_data["header"] is not None else ""
            )

            await send_template_message(message.to, header_text, sections)
        elif message_data["type"] == "image":
            caption_text = message_data["caption"]
            media_id = message_data["media_id"]
            await send_image_message(
                message.to, caption=caption_text, media_id=media_id
            )
        elif message_data["type"] == "catalog":
            body_text = message_data["body"]
            footer_text = message_data["footer"]
            catalog_id = message_data["catalog"]
            product_id = message_data["product"]
            await send_catalog_message(
                message.to, body_text, footer_text, catalog_id, product_id
            )
        elif message_data["type"] == "location":
            await send_location_request_message(message.to, message_data["body"])
    else:
        await send_rapid_message(message.to, message_data)
    return Response("success", status_code=200)


@app.post("/send-email")
async def send_email(message: RapidProEmailMessage):
    try:
        # Create the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = TO_EMAIL_ADDRESS  # You can change this to the recipient's email
        msg["Subject"] = "New RapidPro Message"

        # Add the message text
        msg.attach(MIMEText(str(message.results), "plain"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [TO_EMAIL_ADDRESS], msg.as_string())

        return {"status": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"status": "Failed to send email", "error": str(e)}


@app.post("/sendToSheet")
def write_to_sheet(message: RapidProEmailMessage):
    try:
        logger.info("In send to sheet kinda")
        logger.info(message)
        logger.info(message.results)
        res = message.results
        row = [
            res["customer_full_name"]["value"],
            res["address"]["value"],
            res["cusstomer_nrc"]["value"],
            message.contact.urn,
            res["email"]["value"],
            res["buiness_name"]["value"],
            res["business_type"]["value"],
            res["crop_type"]["value"],
            res["documentation"]["value"],
            res["market_for_crops"]["value"],
            res["financing_requirements"]["value"],
            res["farm_hectorage"]["value"],
            res["mechanization_requirement"]["value"],
            res["mechanization_type"]["value"],
            res["water_resources"]["value"],
        ]
        values = [value["value"] for key, value in message.results.items()]
        values.append(message.contact.urn)
        sheet.append_row(row)
    except Exception as e:
        return {"status": "Failed to write to sheet", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
