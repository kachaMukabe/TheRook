import re
import httpx
import os

from dotenv import load_dotenv
from typing import List
from models import Message, MetaData, Status, WebhookMessage
from pangea_client import check_url, redact_message, scan_file

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")


async def handle_whatsapp_message(message: WebhookMessage):
    if not message.entry:
        return

    if not message.entry[0].changes:
        return

    changes = message.entry[0].changes
    change_field = changes[0].field

    metadata = changes[0].value.metadata
    contacts = changes[0].value.contacts
    messages = changes[0].value.messages
    statuses = changes[0].value.statuses

    if messages:
        await handle_messages(messages, metadata)
    if statuses:
        handle_statuses(statuses)


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


async def handle_messages(messages: List[Message], metadata: MetaData):
    message = messages[0]
    match message.type:
        case "text":
            print("text")
            urls = extract_urls(message.text.body)
            count, redacted_text = redact_message(message.text.body)
            if count > 0:
                await send_message(
                    metadata.phone_number_id,
                    message,
                    f"This is an automated message, please note a unmasked card number has been detected in this message, kindly delete it and always use the following way of sending card numbers in messages. \n {redacted_text}",
                )
            for url in urls:
                verdict, score = check_url(url)
                if verdict == "malicious":
                    await send_message(
                        metadata.phone_number_id,
                        message,
                        f"This is an automated message. This URL: {url} is malicious. Kindly do not click on it and delete the message with it",
                    )

        case "reaction":
            print("reaction")
        case "image":
            media_url = await get_media_url(message.image.id)
            content = await download_media(media_url)
            if content:
                poll_url = scan_file(content, f"{message.image.id}.jpeg")
        case "document":
            media_url_body = await get_media_url(message.image.id)
            print(media_url_body)
        case "sticker":
            print("sticker")
        case "unkown":
            print("unkown")
        case "button":
            print("button")
        case "list_reply":
            print("list reply")
        case "button_reply":
            print("Button reply")
        case _:
            print("Other")


def handle_statuses(statuses: List[Status]):
    print(statuses)
