#!/usr/bin/env python
"""
Complete NEMWEB data discovery - captures ALL fields from all tables.
Downloads samples from each data source to build comprehensive field documentation.
"""

import asyncio
import csv
import io
import json
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
CONCURRENT_DOWNLOADS = 3  # Limit concurrent downloads to be respectful


class NEMWEBCompleteDiscovery:
    """Complete discovery of all NEMWEB tables and fields."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.all_tables = {}  # Full table definitions with all fields
        self.data_sources = {}  # Track data sources and their files

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_directory_listing(self, url: str) -> list[dict]:
        """Fetch and parse directory listing from NEMWEB."""
        logger.info(f"Fetching: {url}")

        try:
            response = await self.client.get(url)
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
                if text == "[To Parent Directory]":
                    continue

                entries.append({"name": text, "href": href, "is_directory": href.endswith("/")})

            return entries

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return []

    async def download_and_parse_csv(self, url: str, source_name: str) -> dict:
        """Download ZIP file and parse all tables and fields from CSV."""
        logger.info(f"Downloading: {url}")

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Extract ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.lower().endswith(".csv")]

                if not csv_files:
                    return {}

                tables = {}

                # Parse each CSV file in the ZIP
                for csv_filename in csv_files:
                    with zf.open(csv_filename) as csv_file:
                        content = csv_file.read().decode("utf-8", errors="ignore")

                        # Parse MMS format
                        reader = csv.reader(io.StringIO(content))

                        for row in reader:
                            if not row or len(row) < 3:
                                continue

                            record_type = row[0].strip().upper()

                            if record_type == "I" and len(row) >= 5:
                                # Table definition - capture ALL fields
                                namespace = row[1].strip() if len(row) > 1 else ""
                                table_name = row[2].strip() if len(row) > 2 else ""

                                # Get ALL field names from position 4 onwards
                                all_fields = []
                                for i in range(4, len(row)):
                                    field = row[i].strip()
                                    if field:  # Only add non-empty fields
                                        all_fields.append(field.upper())

                                full_table_name = f"{namespace}_{table_name}".upper()

                                if full_table_name not in tables:
                                    tables[full_table_name] = {
                                        "namespace": namespace.upper(),
                                        "table_name": table_name.upper(),
                                        "fields": all_fields,
                                        "field_count": len(all_fields),
                                        "source": source_name,
                                        "sample_url": url,
                                        "csv_file": csv_filename,
                                    }

                return tables

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return {}

    async def discover_all_sources(self):
        """Discover all data sources and their tables."""
        # Get main directory listing
        entries = await self.fetch_directory_listing(NEMWEB_CURRENT_URL)

        # Process each subdirectory
        for entry in entries:
            if entry["is_directory"]:
                subdir_name = entry["name"].rstrip("/")
                subdir_url = NEMWEB_CURRENT_URL + subdir_name + "/"

                # Get files in subdirectory
                subentries = await self.fetch_directory_listing(subdir_url)
                zip_files = [e for e in subentries if e["name"].endswith(".zip")]

                if zip_files:
                    self.data_sources[subdir_name] = {
                        "file_count": len(zip_files),
                        "sample_files": [f["name"] for f in zip_files[:5]],
                    }

                    # Download multiple samples to ensure we get all table variations
                    # Some tables only appear in certain files
                    samples_to_download = min(3, len(zip_files))  # Download up to 3 samples

                    for i in range(samples_to_download):
                        sample_url = subdir_url + zip_files[i]["name"]
                        tables = await self.download_and_parse_csv(sample_url, subdir_name)

                        # Merge tables, keeping the most complete field list
                        for table_name, table_info in tables.items():
                            if table_name not in self.all_tables:
                                self.all_tables[table_name] = table_info
                            else:
                                # If we find a version with more fields, use that
                                if len(table_info["fields"]) > len(self.all_tables[table_name]["fields"]):
                                    self.all_tables[table_name] = table_info

                        # Small delay to be respectful
                        await asyncio.sleep(0.5)

        logger.info(f"Discovery complete. Found {len(self.all_tables)} unique tables")

    def generate_markdown_documentation(self) -> str:
        """Generate comprehensive markdown documentation with ALL fields."""
        doc = []
        doc.append("# NEMWEB Complete Data Catalog")
        doc.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        doc.append("## Overview\n")
        doc.append("Complete catalog of all NEMWEB data tables and fields. ")
        doc.append("This document lists EVERY field in every table for easy searching and reference.\n")

        # Summary
        doc.append("## Summary\n")
        doc.append(f"- **Total Data Sources**: {len(self.data_sources)}")
        doc.append(f"- **Total Unique Tables**: {len(self.all_tables)}")

        total_fields = sum(t["field_count"] for t in self.all_tables.values())
        doc.append(f"- **Total Fields Documented**: {total_fields}\n")

        # Quick index by namespace
        doc.append("## Table Index by Namespace\n")
        by_namespace = defaultdict(list)
        for table_name, info in self.all_tables.items():
            by_namespace[info["namespace"]].append(table_name)

        for namespace in sorted(by_namespace.keys()):
            tables = sorted(by_namespace[namespace])
            doc.append(f"- **{namespace}** ({len(tables)} tables): {', '.join(tables[:5])}")
            if len(tables) > 5:
                doc.append(f"  ... and {len(tables) - 5} more")
            doc.append("")

        # Complete field reference
        doc.append("\n## Complete Field Reference\n")
        doc.append("All fields across all tables for easy searching:\n")

        # Collect all unique fields
        all_fields = set()
        field_to_tables = defaultdict(list)

        for table_name, info in self.all_tables.items():
            for field in info["fields"]:
                all_fields.add(field)
                field_to_tables[field].append(table_name)

        doc.append(f"### Total Unique Fields: {len(all_fields)}\n")

        # List common fields (appearing in many tables)
        common_fields = [(f, len(tables)) for f, tables in field_to_tables.items() if len(tables) > 5]
        common_fields.sort(key=lambda x: x[1], reverse=True)

        if common_fields:
            doc.append("### Most Common Fields\n")
            for field, count in common_fields[:20]:
                doc.append(f"- **{field}**: appears in {count} tables")
            doc.append("")

        # Full table documentation
        doc.append("\n## Complete Table Documentation\n")

        # Group by namespace for organization
        for namespace in sorted(by_namespace.keys()):
            doc.append(f"\n### Namespace: {namespace}\n")

            for table_name in sorted(by_namespace[namespace]):
                info = self.all_tables[table_name]

                doc.append(f"\n#### {table_name}\n")
                doc.append(f"- **Namespace**: {info['namespace']}")
                doc.append(f"- **Table**: {info['table_name']}")
                doc.append(f"- **Source**: {info['source']}")
                doc.append(f"- **Field Count**: {info['field_count']}")
                doc.append(f"- **Sample File**: {info.get('csv_file', 'N/A')}")
                doc.append("\n**Complete Field List:**")
                doc.append("```")

                # List ALL fields, formatted nicely
                for i, field in enumerate(info["fields"], 1):
                    doc.append(f"{i:3}. {field}")

                doc.append("```\n")

        # Add field cross-reference at the end
        doc.append("\n## Field Cross-Reference\n")
        doc.append("Quick lookup: which tables contain specific fields\n")

        # Group fields alphabetically
        for field in sorted(all_fields):
            tables = field_to_tables[field]
            if len(tables) <= 10:  # Only show fields that appear in 10 or fewer tables
                doc.append(f"- **{field}**: {', '.join(sorted(tables))}")

        return "\n".join(doc)

    def generate_json_catalog(self) -> str:
        """Generate JSON catalog for programmatic use."""
        catalog = {
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_sources": len(self.data_sources),
                "total_tables": len(self.all_tables),
                "total_fields": sum(t["field_count"] for t in self.all_tables.values()),
            },
            "data_sources": self.data_sources,
            "tables": self.all_tables,
        }

        return json.dumps(catalog, indent=2)


async def main():
    """Main execution function."""
    discovery = NEMWEBCompleteDiscovery()

    try:
        logger.info("Starting complete NEMWEB discovery...")
        await discovery.discover_all_sources()

        # Generate markdown documentation
        markdown_doc = discovery.generate_markdown_documentation()

        # Save markdown
        docs_dir = Path(__file__).parent.parent / "docs"
        docs_dir.mkdir(exist_ok=True)

        md_path = docs_dir / "nemweb_complete_catalog.md"
        with open(md_path, "w") as f:
            f.write(markdown_doc)

        logger.info(f"Markdown documentation saved to: {md_path}")

        # Also save JSON for programmatic use
        json_catalog = discovery.generate_json_catalog()
        json_path = docs_dir / "nemweb_catalog.json"

        with open(json_path, "w") as f:
            f.write(json_catalog)

        logger.info(f"JSON catalog saved to: {json_path}")

        # Print summary
        print(f"\n{'='*60}")
        print("NEMWEB Complete Discovery Finished!")
        print(f"{'='*60}")
        print(f"Total data sources: {len(discovery.data_sources)}")
        print(f"Total unique tables: {len(discovery.all_tables)}")
        print(f"Total fields documented: {sum(t['field_count'] for t in discovery.all_tables.values())}")
        print("\nDocumentation saved to:")
        print(f"  - Markdown: {md_path}")
        print(f"  - JSON: {json_path}")

    finally:
        await discovery.close()


if __name__ == "__main__":
    asyncio.run(main())
