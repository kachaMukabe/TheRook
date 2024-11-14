import re
import httpx
import os
import sys
import logging
from pprint import pprint

from dotenv import load_dotenv
from typing import List
from models import Message, MetaData, Status, WebhookMessage, Section, ProductSection

# from pangea_client import check_url, redact_message, scan_file

load_dotenv()

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

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")
BUSINESS_PHONE_ID = os.getenv("BUSINESS_PHONE_ID")
RAPID_PRO_URL = os.getenv("RAPID_PRO_URL")


async def handle_whatsapp_message(message: WebhookMessage):
    if not message.entry:
        return

    if not message.entry[0].changes:
        return

    # pprint(message)

    changes = message.entry[0].changes
    change_field = changes[0].field

    metadata = changes[0].value.metadata
    contacts = changes[0].value.contacts
    messages = changes[0].value.messages
    # statuses = changes[0].value.statuses if changes[0].value.statuses else None

    if messages:
        print("Handle message")
        logging.info("Handle message")
        await handle_messages(messages, metadata)
    # if statuses:
    #    print("Handle status")
    #    handle_statuses(statuses)


# [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15550785330', 'phone_number_id': '103460055715834'}, 'contacts': [{'profile': {'name': 'Kacha'}, 'wa_id': '260966581925'}], 'messages': [{'from': '260966581925', 'id': 'wamid.HBgMMjYwOTY2NTgxOTI1FQIAEhgUM0ExNURBMjY1QTM2MDkyMDIxMUEA', 'timestamp': '1725532731', 'text': {'body': 'Welcome'}, 'type': 'text'}]}, 'field': 'messages'}]


def extract_urls(text):
    # Regular expression pattern to match URLs
    url_pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)

    # Extract the first element of each tuple in the list of URLs
    urls = [url[0] for url in urls]

    return urls


async def get_media_url(media_id: str):
    url = f"https://graph.facebook.com/v19.0/{media_id}/"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    media_url = ""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print(response)
        print(response.json())
        media_url = response.json()["url"]
    return media_url


async def download_media(url: str):
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.content
    return None


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


async def send_rapid_message(to_user, response_text):
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "text",
        "text": {"body": response_text},
    }
    print(message_data)
    logging.info(message_data)
    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_interactive_list(
    to_user, header_text, text, footer_text, button_text, sections: List[Section]
):

    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header_text},
            "body": {"text": text},
            "footer": {"text": footer_text},
            "action": {
                "sections": [section.model_dump() for section in sections],
                "button": button_text,
            },
        },
    }
    logging.info("Interactive message data")
    logging.info(message_data)

    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_image_message(to_user, caption, media_id=None, media_url=None):
    image = (
        {"id": media_id, "caption": caption}
        if media_id
        else {"link": media_url, "caption": caption}
    )
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "image",
        "image": image,
    }

    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_catalog_message(
    to_user, text, footer_text, catalog_id="1845677735916982", product_id="3ry85up32o"
):
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "interactive",
        "interactive": {
            "type": "product",
            "body": {"text": text},
            "footer": {"text": footer_text},
            "action": {"catalog_id": catalog_id, "product_retailer_id": product_id},
        },
    }

    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_template_message(to_user, header_text, sections: List[ProductSection]):
    message_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_user,
            "type": "template",
            "template": {
                "name": "view_specific_items",
                "language": {
                    "code": "en"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "text",
                                "text": header_text
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "mpm",
                        "index": 0,
                        "parameters": [
                            {
                                "type": "action",
                                "action": {
                                    "thumbnail_product_retailer_id": sections[0].product_items[0].product_retailer_id,
                                    "sections": [section.model_dump() for section in sections]
                                }
                            }
                        ]
                    }
                ]
            }
    }

    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()

async def send_location_request_message(to_user, text):
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "to": to_user,
        "interactive": {
            "type": "location_request_message",
            "body": {"text": text},
            "action": {"name": "send_location"},
        },
    }

    url = f"https://graph.facebook.com/v20.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def handle_messages(messages: List[Message], metadata: MetaData):
    message = messages[0]
    if message.type == "text":
        print("text")
        logging.info("text")
        #            count, redacted_text = redact_message(message.text.body)
        #            if count > 0:
        url = f"{RAPID_PRO_URL}/receive?text={message.text.body}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print(response)
            logging.info(response)
    elif message.type == "reaction":
        media_url = await get_media_url(message.image.id)
        content = await download_media(media_url)
    elif message.type == "image":
        pass
    elif message.type == "interactive":
        url = f"{RAPID_PRO_URL}/receive?text={message.interactive.list_reply.id}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print(response)
            logging.info(response)
    elif message.type == "location":
        url = f"{RAPID_PRO_URL}/receive?text={message.location.latitude},{message.location.longitude}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print(response)
            logging.info(response)
    elif message.type == "order":
        url = f"{RAPID_PRO_URL}/receive?text=order_{message.order.catalog_id}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print(response)
            logging.info(response)
        # await send_message(
        #    metadata.phone_number_id,
        #    message,
        #    "Your order has been placed. You will recieve a payment link shortly",
        #)
    else:
        pass
    # match message.type:
    #     case "text":
    #         print("text")
    #         #            count, redacted_text = redact_message(message.text.body)
    #         #            if count > 0:
    #         url = f"http://rapid.boroma.site/c/ex/c07fae3b-38ff-4e61-bc74-29b38d13f056/receive?text={message.text.body}&sender={message.from_user}"
    #         async with httpx.AsyncClient() as client:
    #             response = await client.get(url)
    #             print(response)
    #         # await send_message(
    #         #    metadata.phone_number_id,
    #         #    message,
    #         #    message.text.body,
    #         # )
    #     #            for url in urls:
    #     #                verdict, score = check_url(url)
    #     #                if verdict == "malicious":
    #     #                    await send_message(
    #     #                        metadata.phone_number_id,
    #     #                        message,
    #     #                        f"This is an automated message. This URL: {url} is malicious. Kindly do not click on it and delete the message with it",
    #     #                    )

    #     case "reaction":
    #         print("reaction")
    #     case "image":
    #         media_url = await get_media_url(message.image.id)
    #         content = await download_media(media_url)
    #         # if content:
    #         # poll_url = scan_file(content, f"{message.image.id}.jpeg")
    #     case "document":
    #         media_url_body = await get_media_url(message.image.id)
    #         print(media_url_body)
    #     case "sticker":
    #         print("sticker")
    #     case "unkown":
    #         print("unkown")
    #     case "button":
    #         print("button")
    #     case "list_reply":
    #         print("list reply")
    #     case "button_reply":
    #         print("Button reply")
    #     case _:
    #         print("Other")


def handle_statuses(statuses: List[Status]):
    print(statuses)
