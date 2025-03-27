import httpx
import os

from dotenv import load_dotenv
from typing import List
from models.webhook import MetaData, WebhookMessage, Message
from models.whatsapp import ProductSection, Section


# from pangea_client import check_url, redact_message, scan_file

load_dotenv()


VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")
BUSINESS_PHONE_ID = os.getenv("BUSINESS_PHONE_ID")
RAPID_PRO_URL = os.getenv("RAPID_PRO_URL")


async def handle_whatsapp_message(req: WebhookMessage, rapid_pro_channel: str):
    if not req.entry:
        return

    if not req.entry[0].changes:
        return

    # pprint(message)

    changes = req.entry[0].changes
    change_field = changes[0].field

    metadata = changes[0].value.metadata
    contacts = changes[0].value.contacts
    messages = changes[0].value.messages
    # statuses = changes[0].value.statuses if changes[0].value.statuses else None

    if messages:
        message = messages[0]
        match message.type:
            case "text":
                await send_to_rapid_pro(
                    message.text.body, message.from_user, rapid_pro_channel
                )
            case "interactive":
                if message.interactive and message.interactive.list_reply:
                    await send_to_rapid_pro(
                        message.interactive.list_reply.id,
                        message.from_user,
                        rapid_pro_channel,
                    )
        # await handle_messages(messages, metadata)
    # if statuses:
    #    print("Handle status")
    #    handle_statuses(statuses)


async def send_to_rapid_pro(text: str, sender: str, channel_id: str):
    url = f"{RAPID_PRO_URL}/{channel_id}/receive?text={text}&sender={sender}"
    print("Rapid url", url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(response)


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
    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_rapid_message(to_user, response_text, business_number):
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "text",
        "text": {"body": response_text},
    }
    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_interactive_list(
    to_user,
    header_text,
    text,
    footer_text,
    button_text,
    sections: List[Section],
    business_number,
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

    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_image_message(
    to_user, business_number, caption, media_id=None, media_url=None
):
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

    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
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

    url = f"https://graph.facebook.com/v22.0/{BUSINESS_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_template_message(
    to_user, header_text, sections: List[ProductSection], business_number
):
    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_user,
        "type": "template",
        "template": {
            "name": "view_specific_items",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [{"type": "text", "text": header_text}],
                },
                {"type": "body", "parameters": []},
                {
                    "type": "button",
                    "sub_type": "mpm",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "action",
                            "action": {
                                "thumbnail_product_retailer_id": sections[0]
                                .product_items[0]
                                .product_retailer_id,
                                "sections": [
                                    section.model_dump() for section in sections
                                ],
                            },
                        }
                    ],
                },
            ],
        },
    }

    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def send_location_request_message(to_user, text, business_number):
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

    url = f"https://graph.facebook.com/v22.0/{business_number}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=message_data)
        response.raise_for_status()


async def handle_messages(messages: List[Message], metadata: MetaData):
    message = messages[0]
    if message.type == "text":
        url = f"{RAPID_PRO_URL}/receive?text={message.text.body}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    elif message.type == "reaction":
        media_url = await get_media_url(message.image.id)
        content = await download_media(media_url)
    elif message.type == "image":
        pass
    elif message.type == "interactive":
        url = f"{RAPID_PRO_URL}/receive?text={message.interactive.list_reply.id}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    elif message.type == "location":
        url = f"{RAPID_PRO_URL}/receive?text={message.location.latitude},{message.location.longitude}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    elif message.type == "order":
        url = f"{RAPID_PRO_URL}/receive?text=order_ {message.order.catalog_id}&sender={message.from_user}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        # await send_message(
        #    metadata.phone_number_id,
        #    message,
        #    "Your order has been placed. You will recieve a payment link shortly",
        # )
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


# def handle_statuses(statuses: List[Status]):
#     print(statuses)
