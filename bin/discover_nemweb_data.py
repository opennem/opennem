#!/usr/bin/env python
"""
Discover and document all NEMWEB data tables and fields.
This script crawls NEMWEB current directory, downloads sample files,
and generates comprehensive documentation of all available data.
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
from urllib.parse import urljoin

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
NEMWEB_BASE_URL = "https://nemweb.com.au/"
NEMWEB_CURRENT_URL = "https://nemweb.com.au/Reports/Current/"
MAX_CONCURRENT_DOWNLOADS = 5
SAMPLE_SIZE_PER_TYPE = 1  # Number of sample files to download per data type


class NEMWEBDiscovery:
    """Discover and analyze NEMWEB data structure."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.data_sources: dict[str, dict] = {}
        self.discovered_tables: dict[str, dict] = {}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_directory_listing(self, url: str) -> list[dict]:
        """Fetch and parse directory listing from NEMWEB."""
        logger.info(f"Fetching directory listing from {url}")

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Parse HTML manually - looking for links
            entries = []
            html_content = response.text

            # Find all anchor tags using regex
            link_pattern = re.compile(r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)

            for match in link_pattern.finditer(html_content):
                href = match.group(1)
                text = match.group(2).strip()

                # Skip parent directory and non-relevant links
                if href in ["/", "../", ""] or text in ["Name", "Last modified", "Size", "Description"]:
                    continue

                # Skip sorting links
                if "?C=" in href or "?M=" in href or "?S=" in href or "?D=" in href:
                    continue

                # Determine if it's a directory or file
                is_directory = href.endswith("/")
                full_url = urljoin(url, href)

                entries.append({"name": text, "href": href, "url": full_url, "is_directory": is_directory})

            return entries

        except Exception as e:
            logger.error(f"Error fetching directory listing from {url}: {e}")
            return []

    async def discover_data_sources(self) -> dict[str, list[str]]:
        """Discover all data sources in NEMWEB current directory."""
        logger.info("Discovering NEMWEB data sources...")

        entries = await self.fetch_directory_listing(NEMWEB_CURRENT_URL)
        data_sources = {}

        for entry in entries:
            if entry["is_directory"]:
                # This is a subdirectory - explore it
                subdirectory_url = entry["url"]
                subdirectory_name = entry["name"].rstrip("/")

                logger.info(f"Exploring subdirectory: {subdirectory_name}")
                subentries = await self.fetch_directory_listing(subdirectory_url)

                # Collect ZIP files in this directory
                zip_files = [e for e in subentries if e["name"].endswith(".zip")]
                if zip_files:
                    data_sources[subdirectory_name] = zip_files
                    logger.info(f"Found {len(zip_files)} ZIP files in {subdirectory_name}")

            elif entry["name"].endswith(".zip"):
                # This is a ZIP file in the root directory
                # Group by report type (extract from filename)
                report_type = self.extract_report_type(entry["name"])
                if report_type not in data_sources:
                    data_sources[report_type] = []
                data_sources[report_type].append(entry)

        self.data_sources = data_sources
        return data_sources

    def extract_report_type(self, filename: str) -> str:
        """Extract report type from filename."""
        # Remove date patterns and extensions
        clean_name = re.sub(r"_\d{8}(_\d{6})?\.zip$", "", filename)
        clean_name = re.sub(r"_\d{8}_\d{8}\.zip$", "", filename)

        # Common patterns
        if "PUBLIC_" in clean_name:
            clean_name = clean_name.replace("PUBLIC_", "")

        return clean_name or "Unknown"

    async def download_and_parse_sample(self, url: str) -> dict | None:
        """Download a sample file and parse its structure."""
        logger.info(f"Downloading sample from {url}")

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Extract ZIP content
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.endswith(".CSV") or f.endswith(".csv")]

                if not csv_files:
                    logger.warning(f"No CSV files found in {url}")
                    return None

                # Parse the first CSV file
                csv_filename = csv_files[0]
                with zf.open(csv_filename) as csv_file:
                    content = csv_file.read().decode("utf-8", errors="ignore")
                    return self.parse_mms_csv_structure(content, url)

        except Exception as e:
            logger.error(f"Error downloading/parsing {url}: {e}")
            return None

    def parse_mms_csv_structure(self, content: str, source_url: str) -> dict:
        """Parse MMS CSV structure to extract tables and fields."""
        tables = {}
        current_table = None

        try:
            reader = csv.reader(io.StringIO(content))

            for row in reader:
                if not row or len(row) < 1:
                    continue

                record_type = row[0].strip().upper()

                if record_type == "I" and len(row) >= 5:
                    # Table definition row
                    namespace = row[1] if len(row) > 1 else ""
                    table_name = row[2] if len(row) > 2 else ""
                    full_table_name = f"{namespace}_{table_name}"

                    # Extract field names (starting from index 4)
                    field_names = [f.strip() for f in row[4:] if f.strip()]

                    if full_table_name not in tables:
                        tables[full_table_name] = {
                            "namespace": namespace,
                            "table_name": table_name,
                            "fields": field_names,
                            "field_types": {},
                            "sample_values": defaultdict(list),
                            "source_url": source_url,
                            "record_count": 0,
                        }
                    current_table = full_table_name

                elif record_type == "D" and current_table and current_table in tables:
                    # Data row - analyze field types from sample values
                    table_info = tables[current_table]
                    values = row[4 : 4 + len(table_info["fields"])]

                    for field, value in zip(table_info["fields"], values, strict=False):
                        if value and len(table_info["sample_values"][field]) < 5:
                            table_info["sample_values"][field].append(value)

                    table_info["record_count"] += 1

        except Exception as e:
            logger.error(f"Error parsing CSV structure: {e}")

        # Infer field types from sample values
        for table_info in tables.values():
            for field, samples in table_info["sample_values"].items():
                table_info["field_types"][field] = self.infer_field_type(samples)

        return tables

    def infer_field_type(self, samples: list[str]) -> str:
        """Infer field type from sample values."""
        if not samples:
            return "unknown"

        # Check for common patterns
        for sample in samples:
            if not sample:
                continue

            # Try to parse as number
            try:
                float(sample)
                if "." in sample:
                    return "float"
                else:
                    return "integer"
            except ValueError:
                pass

            # Check for datetime patterns
            if re.match(r"\d{4}/\d{2}/\d{2}", sample) or re.match(r"\d{2}/\d{2}/\d{4}", sample):
                return "date"
            if re.match(r"\d{2}:\d{2}:\d{2}", sample):
                return "time"
            if "T" in sample and ":" in sample:
                return "datetime"

            # Default to string
            return "string"

        return "unknown"

    def analyze_update_frequency(self, files: list[dict]) -> dict:
        """Analyze update frequency from file timestamps."""
        if not files:
            return {"frequency": "unknown", "file_count": 0}

        # Extract timestamps from filenames
        timestamps = []
        for file_info in files:
            filename = file_info["name"]

            # Common date patterns in NEMWEB files
            date_match = re.search(r"(\d{8})(_\d{6})?", filename)
            if date_match:
                date_str = date_match.group(1)
                try:
                    date = datetime.strptime(date_str, "%Y%m%d")
                    timestamps.append(date)
                except Exception:
                    pass

        if len(timestamps) < 2:
            return {"frequency": "unknown", "file_count": len(files)}

        # Calculate average interval
        timestamps.sort()
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600  # in hours
            intervals.append(interval)

        if not intervals:
            return {"frequency": "unknown", "file_count": len(files)}

        avg_interval = sum(intervals) / len(intervals)

        # Determine frequency category
        if avg_interval < 0.5:
            frequency = "5-minute"
        elif avg_interval < 1.5:
            frequency = "hourly"
        elif avg_interval < 25:
            frequency = "daily"
        elif avg_interval < 170:
            frequency = "weekly"
        else:
            frequency = "monthly"

        return {"frequency": frequency, "avg_interval_hours": round(avg_interval, 2), "file_count": len(files)}

    async def discover_all(self):
        """Main discovery process."""
        # Discover data sources
        await self.discover_data_sources()

        # Download and analyze samples from each data source
        for source_name, files in self.data_sources.items():
            logger.info(f"\nAnalyzing {source_name}...")

            # Analyze update frequency
            frequency_info = self.analyze_update_frequency(files)

            # Download samples (limit to avoid overwhelming)
            sample_files = files[: min(SAMPLE_SIZE_PER_TYPE, len(files))]

            for file_info in sample_files:
                tables = await self.download_and_parse_sample(file_info["url"])

                if tables:
                    for table_name, table_info in tables.items():
                        if table_name not in self.discovered_tables:
                            self.discovered_tables[table_name] = table_info
                            self.discovered_tables[table_name]["source_type"] = source_name
                            self.discovered_tables[table_name]["update_frequency"] = frequency_info

        logger.info(f"\nDiscovery complete. Found {len(self.discovered_tables)} unique tables.")

    def generate_markdown_documentation(self) -> str:
        """Generate comprehensive markdown documentation."""
        doc = []
        doc.append("# NEMWEB Data Documentation")
        doc.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        doc.append("## Overview\n")
        doc.append(
            "This document provides a comprehensive overview of all data available through NEMWEB's public directory listings.\n"
        )
        doc.append("NEMWEB publishes energy market data in CSV format, packaged in ZIP files. ")
        doc.append("Each CSV file can contain multiple tables, identified by record type markers (C, I, D).\n")

        # Summary statistics
        doc.append("## Summary Statistics\n")
        doc.append(f"- **Total Data Sources**: {len(self.data_sources)}")
        doc.append(f"- **Total Unique Tables**: {len(self.discovered_tables)}")

        # Group tables by namespace
        tables_by_namespace = defaultdict(list)
        for table_name, table_info in self.discovered_tables.items():
            namespace = table_info.get("namespace", "Unknown")
            tables_by_namespace[namespace].append((table_name, table_info))

        doc.append(f"- **Total Namespaces**: {len(tables_by_namespace)}\n")

        # Data sources overview
        doc.append("## Data Sources\n")
        doc.append("| Source | Files Count | Update Frequency | Description |")
        doc.append("|--------|-------------|------------------|-------------|")

        for source_name, files in sorted(self.data_sources.items()):
            frequency_info = self.analyze_update_frequency(files)
            doc.append(f"| {source_name} | {len(files)} | {frequency_info['frequency']} | Energy market data |")

        # Detailed table documentation
        doc.append("\n## Table Documentation\n")

        for namespace in sorted(tables_by_namespace.keys()):
            doc.append(f"\n### Namespace: {namespace}\n")

            for table_name, table_info in sorted(tables_by_namespace[namespace]):
                doc.append(f"\n#### Table: `{table_name}`\n")

                # Table metadata
                doc.append(f"- **Source Type**: {table_info.get('source_type', 'Unknown')}")

                freq_info = table_info.get("update_frequency", {})
                doc.append(f"- **Update Frequency**: {freq_info.get('frequency', 'Unknown')}")
                doc.append(f"- **Field Count**: {len(table_info.get('fields', []))}")

                # Field documentation
                doc.append("\n**Fields:**\n")
                doc.append("| Field Name | Data Type | Description |")
                doc.append("|------------|-----------|-------------|")

                fields = table_info.get("fields", [])
                field_types = table_info.get("field_types", {})

                for field in fields:
                    field_type = field_types.get(field, "unknown")
                    # Add common field descriptions based on field name
                    description = self.get_field_description(field)
                    doc.append(f"| {field} | {field_type} | {description} |")

                doc.append("")

        # Additional information
        doc.append("\n## Data Access\n")
        doc.append("All data can be accessed through the NEMWEB public directory:")
        doc.append(f"- Current data: {NEMWEB_CURRENT_URL}")
        doc.append("- Archive data: https://nemweb.com.au/Reports/Archive/\n")

        doc.append("## File Format\n")
        doc.append("NEMWEB CSV files use a multi-table format with the following record types:")
        doc.append("- **C**: Comment/metadata record")
        doc.append("- **I**: Table information record (defines table name and fields)")
        doc.append("- **D**: Data record (contains actual data values)\n")

        return "\n".join(doc)

    def get_field_description(self, field_name: str) -> str:
        """Get field description based on common field names."""
        field_lower = field_name.lower()

        common_fields = {
            "duid": "Dispatchable Unit Identifier",
            "regionid": "Region Identifier (e.g., NSW1, VIC1)",
            "settlementdate": "Settlement date and time",
            "interval_datetime": "Interval date and time",
            "rrp": "Regional Reference Price ($/MWh)",
            "totaldemand": "Total demand (MW)",
            "availablegeneration": "Available generation capacity (MW)",
            "initialmw": "Initial MW output",
            "totalcleared": "Total cleared amount",
            "pasaavailability": "PASA availability (MW)",
            "maxavail": "Maximum available capacity (MW)",
            "rampuprate": "Ramp up rate (MW/min)",
            "rampdownrate": "Ramp down rate (MW/min)",
            "dispatchtype": "Type of dispatch",
            "agcstatus": "AGC Status",
            "dispatch": "Dispatch value",
            "predispatch": "Pre-dispatch value",
            "semidispatch": "Semi-dispatch flag",
            "lastchanged": "Last changed timestamp",
            "versionno": "Version number",
            "periodid": "Period identifier",
            "runno": "Run number",
            "participantid": "Participant identifier",
        }

        for key, desc in common_fields.items():
            if key in field_lower:
                return desc

        return "Field description"


async def main():
    """Main execution function."""
    discovery = NEMWEBDiscovery()

    try:
        # Run discovery
        await discovery.discover_all()

        # Generate documentation
        documentation = discovery.generate_markdown_documentation()

        # Save documentation
        output_path = Path(__file__).parent.parent / "docs" / "nemweb_data_catalog.md"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w") as f:
            f.write(documentation)

        logger.info(f"\nDocumentation saved to: {output_path}")

        # Print summary
        print(f"\n{'=' * 60}")
        print("NEMWEB Data Discovery Complete!")
        print(f"{'=' * 60}")
        print(f"Total data sources discovered: {len(discovery.data_sources)}")
        print(f"Total unique tables found: {len(discovery.discovered_tables)}")
        print(f"Documentation saved to: {output_path}")

    finally:
        await discovery.close()


if __name__ == "__main__":
    asyncio.run(main())
