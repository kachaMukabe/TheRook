import os
import smtplib
import yaml
import gspread
from fastapi import APIRouter, Response
from config import get_store
from models.business import Business
from models.rapidpro import RapidProCallback, RapidProEmailMessage
from models.whatsapp import ProductSection, Section
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials
from message_handler import (
    send_location_request_message,
    send_rapid_message,
    send_interactive_list,
    send_image_message,
    send_catalog_message,
    send_template_message,
)
import utils

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


router = APIRouter(prefix="/rapidpro", tags=["Rapidpro"])


@router.post("/callback")
async def rapid_pro_callback(message: RapidProCallback):

    try:
        message_data = yaml.safe_load(message.text)
    except Exception as e:
        message_data = message.text

    with get_store() as session:
        user = (
            session.query(object_type=Business)
            .where_equals("phone_number", message.from_no_plus)
            .first()
        )
        if type(message_data) is dict:
            if message_data["type"] == "interactive":
                sections = [
                    Section.model_validate(section)
                    for section in message_data["sections"]
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
                    user.business_id,
                )
            elif message_data["type"] == "template":
                sections = [
                    ProductSection.model_validate(section)
                    for section in message_data["sections"]
                ]
                header_text = (
                    message_data["header"] if message_data["header"] is not None else ""
                )

                await send_template_message(
                    message.to, header_text, sections, user.business_id
                )
            elif message_data["type"] == "image":
                caption_text = message_data["caption"]
                media_id = message_data["media_id"]
                await send_image_message(
                    message.to,
                    user.business_id,
                    caption=caption_text,
                    media_id=media_id,
                )
            elif message_data["type"] == "catalog":
                body_text = message_data["body"]
                footer_text = message_data["footer"]
                catalog_id = message_data["catalog"]
                product_id = message_data["product"]
                await send_catalog_message(
                    message.to,
                    body_text,
                    footer_text,
                    catalog_id,
                    product_id,
                )
            elif message_data["type"] == "location":
                await send_location_request_message(
                    message.to, message_data["body"], user.business_id
                )
        else:
            await send_rapid_message(message.to, message_data, user.business_id)
    return Response("success", status_code=200)


@router.post("/send-email")
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
        utils.logger.error(f"Failed to send email: {e}")
        return {"status": "Failed to send email", "error": str(e)}


@router.post("/sendToSheet")
def write_to_sheet(message: RapidProEmailMessage):
    try:
        utils.logger.info("In send to sheet kinda")
        utils.logger.info(message)
        utils.logger.info(message.results)
        res = message.results
        row = [
            res["customer_full_name"]["value"],
            res["address"]["value"],
            res["customer_nrc"]["value"],
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
