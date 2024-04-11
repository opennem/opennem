#!/usr/bin/env python
#
# script to delete all dns records for a zone in cloudflare
#
# usage:
# cloudflare_delete_dns.py <domain> [api_token]
#
# api_token is optional, if not provided, it will be read from the CLOUDFLARE_API_TOKEN environment variable
#

import logging
import os

import CloudFlare

logging.basicConfig(level=logging.INFO, format="[%(asctime)s  %(levelname)s] %(message)s")

logger = logging.getLogger("cloudflare_delete_dns")


def remove_all_dns_records(domain: str, api_token: str | None = None) -> None:
    if not api_token:
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not api_token:
        logger.error("API token not provided")
        return

    cf = CloudFlare.CloudFlare(token=api_token)

    # Get the zone ID for the domain
    try:
        zones = cf.zones.get(params={"name": domain})
        zone_id = zones[0]["id"]
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logger.error(f"Error retrieving zone ID: {e}")
        return

    # Get all DNS records for the zone
    try:
        dns_records = cf.zones.dns_records.get(zone_id)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logger.error(f"Error retrieving DNS records: {e}")
        return

    # Delete each DNS record
    for record in dns_records:
        record_id = record["id"]
        try:
            cf.zones.dns_records.delete(zone_id, record_id)
            logger.info(f"Deleted DNS record: {record['name']} ({record['type']})")
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            logger.error(f"Error deleting DNS record: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.error(f"Usage: {sys.argv[0]} <domain> [api_token]")
        sys.exit(1)

    domain = sys.argv[1]

    api_token = None

    if len(sys.argv) == 3:
        api_token = sys.argv[2]

    remove_all_dns_records(domain, api_token)
