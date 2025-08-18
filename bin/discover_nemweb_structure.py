#!/usr/bin/env python
"""
Quick discovery of NEMWEB data structure.
Lists all available data sources and downloads a few samples to understand structure.
"""

import asyncio
import csv
import io
import logging
import re
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NEMWEB_CURRENT_URL = "https://nemweb.com.au/Reports/Current/"


async def fetch_directory_listing(url: str) -> list[dict]:
    """Fetch and parse directory listing from NEMWEB."""
    logger.info(f"Fetching: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            entries = []
            html_content = response.text

            # Find all anchor tags
            link_pattern = re.compile(r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)

            for match in link_pattern.finditer(html_content):
                href = match.group(1)
                text = match.group(2).strip()

                # Skip irrelevant links
                if href in ["/", "../", ""] or text in ["Name", "Last modified", "Size", "Description"]:
                    continue
                if "?C=" in href or "?M=" in href or "?S=" in href or "?D=" in href:
                    continue

                entries.append({"name": text, "href": href, "is_directory": href.endswith("/")})

            return entries

        except Exception as e:
            logger.error(f"Error: {e}")
            return []


async def download_sample(url: str) -> dict | None:
    """Download and parse a sample ZIP file."""
    logger.info(f"Downloading sample: {url}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            # Extract and parse CSV
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.lower().endswith(".csv")]

                if not csv_files:
                    return None

                tables = {}
                with zf.open(csv_files[0]) as csv_file:
                    content = csv_file.read().decode("utf-8", errors="ignore")
                    reader = csv.reader(io.StringIO(content))

                    for row in reader:
                        if not row or len(row) < 3:
                            continue

                        record_type = row[0].strip().upper()

                        if record_type == "I" and len(row) >= 5:
                            # Table definition
                            namespace = row[1]
                            table_name = row[2]
                            fields = [f.strip() for f in row[4:] if f.strip()]

                            full_name = f"{namespace}_{table_name}"
                            tables[full_name] = {
                                "namespace": namespace,
                                "table": table_name,
                                "fields": fields,
                                "field_count": len(fields),
                            }

                return tables

        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None


async def main():
    """Main discovery function."""
    # Get main directory listing
    entries = await fetch_directory_listing(NEMWEB_CURRENT_URL)

    data_sources = {}
    all_tables = {}

    # Process each subdirectory
    for entry in entries:
        if entry["is_directory"]:
            subdir_name = entry["name"].rstrip("/")
            # Skip parent directory link
            if subdir_name == "[To Parent Directory]" or entry["href"] == "../":
                continue
            subdir_url = NEMWEB_CURRENT_URL + subdir_name + "/"

            # Get files in subdirectory
            subentries = await fetch_directory_listing(subdir_url)
            zip_files = [e for e in subentries if e["name"].endswith(".zip")]

            if zip_files:
                data_sources[subdir_name] = {"file_count": len(zip_files), "sample_files": [f["name"] for f in zip_files[:3]]}

                # Download one sample to understand structure
                if zip_files and subdir_name not in ["Bidmove_Complete", "Bidmove_Summary", "Billing", "Causer_Pays"]:
                    sample_url = NEMWEB_CURRENT_URL + subdir_name + "/" + zip_files[0]["name"]
                    tables = await download_sample(sample_url)

                    if tables:
                        for table_name, table_info in tables.items():
                            if table_name not in all_tables:
                                all_tables[table_name] = table_info
                                all_tables[table_name]["source"] = subdir_name

    # Generate markdown documentation
    output_path = Path(__file__).parent.parent / "docs" / "nemweb_data_structure.md"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        f.write("# NEMWEB Data Structure\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

        f.write("## Data Sources\n\n")
        f.write("| Source | File Count | Sample Files |\n")
        f.write("|--------|------------|-------------|\n")

        for source, info in sorted(data_sources.items()):
            samples = ", ".join(info["sample_files"][:2])
            f.write(f"| {source} | {info['file_count']} | {samples} |\n")

        f.write("\n## Discovered Tables\n\n")

        # Group tables by namespace
        by_namespace = defaultdict(list)
        for table_name, info in all_tables.items():
            by_namespace[info["namespace"]].append((table_name, info))

        for namespace in sorted(by_namespace.keys()):
            f.write(f"\n### {namespace}\n\n")

            for table_name, info in sorted(by_namespace[namespace]):
                f.write(f"#### {info['table']}\n")
                f.write(f"- **Full Name**: `{table_name}`\n")
                f.write(f"- **Source**: {info['source']}\n")
                f.write(f"- **Field Count**: {info['field_count']}\n")
                f.write(f"- **Fields**: {', '.join(info['fields'][:10])}")
                if len(info["fields"]) > 10:
                    f.write(f" ... and {len(info['fields']) - 10} more")
                f.write("\n\n")

    logger.info(f"Documentation saved to: {output_path}")

    # Print summary
    print("\nDiscovery Complete!")
    print(f"Found {len(data_sources)} data sources")
    print(f"Discovered {len(all_tables)} unique tables")
    print(f"Documentation: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
