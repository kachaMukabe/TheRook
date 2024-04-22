import os

import pangea.exceptions as pe
from dotenv import load_dotenv

from pangea.config import PangeaConfig
from pangea.services.intel import (
    URLReputationBulkRequest,
    UrlIntel,
    URLReputationResult,
)
from pangea.services.redact import Redact
from pangea.services.file_scan import FileScan

load_dotenv()

# Load client configuration from environment variables `PANGEA_AUDIT_TOKEN` and
# `PANGEA_DOMAIN`.
token = os.getenv("PANGEA_AUDIT_TOKEN")
assert token
domain = os.getenv("PANGEA_DOMAIN")
assert domain
config = PangeaConfig(domain=domain)
intel = UrlIntel(token, config=config)
redact = Redact(token, config=config)
file_client = FileScan(token, config=config)


def check_url(url: str):
    try:
        response = intel.reputation_bulk(
            [url], provider="crowdstrike", verbose=True, raw=True
        )
        verdict = response.result.data[url].verdict
        score = response.result.data[url].score
        category = response.result.data[url].category
        return verdict, score
    except pe.PangeaAPIException as e:
        print(e)
    return None, None


def redact_message(text: str):
    try:
        response = redact.redact(text, rules=["CREDIT_CARD", "PROFANITY"])
        count = response.result.count
        redacted_text = response.result.redacted_text
        return count, redacted_text
    except pe.PangeaAPIException as e:
        print(e)
    return 0, None


def scan_file(file_path: str):
    try:
        with open(file_path, "rb") as f:
            response = file_client.file_scan(
                file=f, verbose=True, provider="crowdstrike"
            )
            print(f"Response: {response.result}")
    except pe.PangeaAPIException as e:
        print(e)
        for err in e.errors:
            print(f"\t{err.detail} \n")


def main():
    print("Checking URL...")

    try:
        indicator = "http://113.235.101.11:54384"
        # response = intel.reputation(
        #    url=indicator, provider="crowdstrike", verbose=True, raw=True
        # )
        verdict, score = check_url(indicator)
        print("Result:")
        print(f"\tIndicator: {indicator}")
        print(f"\t\tVerdict: {verdict}")
        print(f"\t\tScore: {score}")
    except pe.PangeaAPIException as e:
        print(e)


if __name__ == "__main__":
    main()
