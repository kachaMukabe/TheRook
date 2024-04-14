import os

import pangea.exceptions as pe
from dotenv import load_dotenv

from pangea.config import PangeaConfig
from pangea.services.intel import (
    URLReputationBulkRequest,
    UrlIntel,
    URLReputationResult,
)

load_dotenv()

# Load client configuration from environment variables `PANGEA_AUDIT_TOKEN` and
# `PANGEA_DOMAIN`.
token = os.getenv("PANGEA_AUDIT_TOKEN")
assert token
domain = os.getenv("PANGEA_DOMAIN")
assert domain
config = PangeaConfig(domain=domain)
intel = UrlIntel(token, config=config)


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
