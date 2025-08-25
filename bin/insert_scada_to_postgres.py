#!/usr/bin/env python3
"""
Efficient AEMO SCADA data insertion into PostgreSQL using DuckDB parser
Implements batch upsert operations for optimal performance
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import asyncpg
import pandas as pd
import requests
from dotenv import load_dotenv
from parse_aemo_mms_duckdb import AEMOMMSParser

# Load environment variables
load_dotenv()


class ScadaDataInserter:
    """Efficiently insert AEMO SCADA data into PostgreSQL facility_scada table"""

    def __init__(self, database_url: str):
        # Convert SQLAlchemy URL to asyncpg format
        self.database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        self.parser = AEMOMMSParser()
        self.conn = None

    async def connect(self):
        """Connect to PostgreSQL database"""
        self.conn = await asyncpg.connect(self.database_url)
        print("Connected to PostgreSQL database")

    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.conn:
            await self.conn.close()
            print("Disconnected from PostgreSQL database")

    async def prepare_scada_data(self, csv_content: str, network_id: str = "NEM") -> pd.DataFrame:
        """
        Parse SCADA data and prepare it for insertion into facility_scada table

        Returns DataFrame with columns matching facility_scada schema
        """
        print("Parsing SCADA data with DuckDB...")
        start = datetime.now()

        # Use the optimized SCADA parser
        scada_df = self.parser.parse_scada_optimized(csv_content)

        if scada_df.empty:
            print("No SCADA data found in file")
            return pd.DataFrame()

        # Rename columns to match database schema
        scada_df = scada_df.rename(columns={"settlementdate": "interval", "duid": "facility_code", "scadavalue": "generated"})

        # Add required columns
        scada_df["network_id"] = network_id
        scada_df["is_forecast"] = False
        scada_df["energy_quality_flag"] = 0

        # Calculate energy (MW to MWh for 5-minute intervals)
        # Energy = Power * Time (5 minutes = 1/12 hour)
        scada_df["energy"] = scada_df["generated"] / 12.0

        # Remove any rows with null intervals or facility codes
        scada_df = scada_df.dropna(subset=["interval", "facility_code"])

        parse_time = (datetime.now() - start).total_seconds() * 1000
        print(f"Prepared {len(scada_df)} records in {parse_time:.2f} ms")

        return scada_df

    async def batch_upsert(self, data: pd.DataFrame, batch_size: int = 1000):
        """
        Perform batch upsert of SCADA data into facility_scada table
        Uses ON CONFLICT to handle duplicates efficiently
        """
        if data.empty:
            print("No data to insert")
            return

        print(f"Starting batch upsert of {len(data)} records...")
        start = datetime.now()

        # Convert DataFrame to list of tuples for insertion
        records = [
            (
                row["interval"],
                row["network_id"],
                row["facility_code"],
                row["generated"] if pd.notna(row["generated"]) else None,
                row["is_forecast"],
                row["energy"] if pd.notna(row["energy"]) else None,
                row["energy_quality_flag"],
            )
            for _, row in data.iterrows()
        ]

        # SQL for upsert operation
        upsert_query = """
            INSERT INTO facility_scada (
                interval, network_id, facility_code, generated,
                is_forecast, energy, energy_quality_flag
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (interval, network_id, facility_code, is_forecast)
            DO UPDATE SET
                generated = EXCLUDED.generated,
                energy = EXCLUDED.energy,
                energy_quality_flag = EXCLUDED.energy_quality_flag
        """

        # Process in batches
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            # Use executemany for batch insertion
            await self.conn.executemany(upsert_query, batch)
            total_inserted += len(batch)

            if total_inserted % 5000 == 0:
                print(f"  Inserted {total_inserted}/{len(records)} records...")

        insert_time = (datetime.now() - start).total_seconds()
        print(f"Successfully upserted {total_inserted} records in {insert_time:.2f} seconds")
        print(f"Rate: {total_inserted / insert_time:.0f} records/second")

    async def process_scada_file(self, url: str, network_id: str = "NEM"):
        """Process a single SCADA file from URL"""
        print(f"\nProcessing: {url}")

        # Download and extract CSV
        print("Downloading file...")
        csv_content = self.parser.download_scada_file(url)

        # Prepare data for insertion
        data = await self.prepare_scada_data(csv_content, network_id)

        if not data.empty:
            # Insert data into database
            await self.batch_upsert(data)

            # Show summary statistics
            print("\nSummary:")
            print(f"  Time range: {data['interval'].min()} to {data['interval'].max()}")
            print(f"  Unique facilities: {data['facility_code'].nunique()}")
            print(f"  Total energy: {data['energy'].sum():.2f} MWh")
            print(f"  Average generation: {data['generated'].mean():.2f} MW")

    async def process_multiple_files(self, urls: list[str], network_id: str = "NEM"):
        """Process multiple SCADA files"""
        await self.connect()

        try:
            for url in urls:
                await self.process_scada_file(url, network_id)
        finally:
            await self.disconnect()

    async def get_latest_scada_urls(self, base_url: str, count: int = 5) -> list[str]:
        """Get the latest SCADA file URLs from AEMO directory"""
        import re

        print(f"Fetching latest files from {base_url}")
        response = requests.get(base_url)
        response.raise_for_status()

        # Parse file names from directory listing (handles both href formats)
        pattern = r"PUBLIC_DISPATCHSCADA_\d+_\d+\.zip"
        matches = re.findall(pattern, response.text)

        # Remove duplicates and sort by timestamp in filename
        unique_files = sorted(set(matches), reverse=True)[:count]

        # Build full URLs
        urls = [base_url + f for f in unique_files]
        print(f"Found {len(urls)} files to process")

        return urls


async def main():
    """Main entry point for SCADA data insertion"""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_HOST_URL")
    if not database_url:
        print("Error: DATABASE_HOST_URL not set in environment")
        return

    # Create inserter instance
    inserter = ScadaDataInserter(database_url)

    # AEMO SCADA directory
    base_url = "https://www.nemweb.com.au/REPORTS/CURRENT/Dispatch_SCADA/"

    # Option 1: Process specific file (for testing)
    # specific_file = "PUBLIC_DISPATCHSCADA_202508201555_0000000477141747.zip"
    # await inserter.process_multiple_files([base_url + specific_file])

    # Option 2: Process latest files
    latest_urls = await inserter.get_latest_scada_urls(base_url, count=5)
    await inserter.process_multiple_files(latest_urls)

    # Example: Process with custom network ID
    # await inserter.process_multiple_files(latest_urls, network_id="WEM")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
