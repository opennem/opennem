#!/usr/bin/env python3
"""
Efficient AEMO MMS CSV parser using DuckDB
Parses facility SCADA data from AEMO's NEMWEB

This approach is 10-100x faster than row-by-row Python parsing
"""

import io
import zipfile
from datetime import datetime

import duckdb
import pandas as pd
import requests


class AEMOMMSParser:
    """Efficient parser for AEMO MMS CSV format using DuckDB"""

    def __init__(self):
        # Create in-memory DuckDB connection
        self.conn = duckdb.connect(":memory:")

    def download_scada_file(self, url: str) -> str:
        """Download and extract CSV from AEMO zip file"""
        response = requests.get(url)
        response.raise_for_status()

        # Extract CSV from zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # AEMO zips typically contain a single CSV
            csv_name = zf.namelist()[0]
            return zf.read(csv_name).decode("utf-8")

    def parse_mms_csv_efficient(self, csv_content: str) -> dict:
        """
        Parse MMS CSV using DuckDB for efficient processing

        Returns dict with table_name -> DataFrame mapping
        """
        tables = {}

        # Step 1: Load raw CSV into DuckDB
        # Split content into lines and load directly
        lines = csv_content.splitlines()
        df_lines = pd.DataFrame({"line": lines})
        self.conn.register("raw_lines_df", df_lines)

        self.conn.execute("""
            CREATE OR REPLACE TABLE raw_data AS
            SELECT * FROM raw_lines_df
            WHERE line IS NOT NULL AND trim(line) != ''
        """)

        # Step 2: Split into lines and parse record types
        self.conn.execute("""
            CREATE OR REPLACE TABLE parsed_lines AS
            SELECT
                row_number() OVER () as line_num,
                string_split(line, ',') as parts,
                CASE
                    WHEN length(string_split(line, ',')) > 0
                    THEN trim(string_split(line, ',')[1])
                    ELSE NULL
                END as record_type
            FROM raw_data
            WHERE line IS NOT NULL AND trim(line) != ''
        """)

        # Step 3: Extract table definitions (I records)
        table_defs = self.conn.execute("""
            SELECT
                line_num,
                parts[2] as namespace,
                parts[3] as table_name,
                list_slice(parts, 5, length(parts)) as field_names
            FROM parsed_lines
            WHERE record_type = 'I'
            ORDER BY line_num
        """).fetchall()

        # Step 4: Process each table
        for _i, (def_line_num, namespace, table_name, field_names) in enumerate(table_defs):
            # Clean field names
            field_names = [f.strip().lower() for f in field_names if f]
            full_table_name = f"{namespace.lower()}_{table_name.lower()}"

            # Find the next table definition line (or end of file)
            next_def_line = self.conn.execute(
                """
                SELECT MIN(line_num)
                FROM parsed_lines
                WHERE record_type = 'I' AND line_num > ?
            """,
                [def_line_num],
            ).fetchone()[0]

            if next_def_line is None:
                # This is the last table
                next_def_line = "999999999"

            # Extract data records for this table
            data_query = f"""
                SELECT list_slice(parts, 5, 5 + {len(field_names)}) as values
                FROM parsed_lines
                WHERE record_type = 'D'
                AND line_num > {def_line_num}
                AND line_num < {next_def_line}
            """

            data_rows = self.conn.execute(data_query).fetchall()

            if data_rows:
                # Create DataFrame efficiently
                df_data = [row[0][: len(field_names)] for row in data_rows]
                df = pd.DataFrame(df_data, columns=field_names)

                # Type conversion for common fields
                if "settlementdate" in df.columns:
                    # AEMO uses format: "YYYY/MM/DD HH:MM:SS"
                    df["settlementdate"] = pd.to_datetime(df["settlementdate"], format="%Y/%m/%d %H:%M:%S", errors="coerce")

                numeric_cols = ["scadavalue", "mw", "price", "value"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                tables[full_table_name] = df

        return tables

    def parse_with_sql(self, csv_content: str, sql_query: str) -> pd.DataFrame:
        """
        Parse MMS CSV and run SQL query directly on the data

        Example SQL:
        SELECT duid, scadavalue, settlementdate
        FROM dispatch_unit_scada
        WHERE scadavalue > 100
        ORDER BY settlementdate
        """
        tables = self.parse_mms_csv_efficient(csv_content)

        # Register all tables in DuckDB
        for table_name, df in tables.items():
            self.conn.register(table_name, df)

        # Execute query and return result
        return self.conn.execute(sql_query).df()

    def parse_scada_optimized(self, csv_content: str) -> pd.DataFrame:
        """
        Optimized parsing specifically for SCADA data
        Uses DuckDB's columnar processing for maximum speed
        """
        # Load the CSV content into DuckDB
        lines = csv_content.splitlines()
        df_lines = pd.DataFrame({"line": lines})
        self.conn.register("scada_raw_lines", df_lines)

        # Direct SQL parsing for SCADA format
        result = self.conn.execute("""
            WITH raw_lines AS (
                SELECT
                    row_number() OVER () as line_num,
                    string_split(line, ',') as parts
                FROM scada_raw_lines
                WHERE trim(line) != ''
            ),
            table_starts AS (
                SELECT
                    line_num,
                    parts[2] as namespace,
                    parts[3] as table_name,
                    list_slice(parts, 5, length(parts)) as columns
                FROM raw_lines
                WHERE trim(parts[1]) = 'I'
            ),
            scada_data AS (
                SELECT
                    TRIM(parts[5], '"') as settlementdate,
                    TRIM(parts[6], '"') as duid,
                    TRY_CAST(TRIM(parts[7], '"') as DOUBLE) as scadavalue
                FROM raw_lines
                WHERE trim(parts[1]) = 'D'
                AND EXISTS (
                    SELECT 1 FROM table_starts
                    WHERE upper(table_name) = 'UNIT_SCADA'
                    AND line_num < raw_lines.line_num
                )
            )
            SELECT
                settlementdate,
                duid,
                scadavalue
            FROM scada_data
            WHERE scadavalue IS NOT NULL
            ORDER BY settlementdate, duid
        """).df()

        # Convert settlementdate to datetime
        if not result.empty and "settlementdate" in result.columns:
            result["settlementdate"] = pd.to_datetime(result["settlementdate"], format="%Y/%m/%d %H:%M:%S", errors="coerce")

        return result


def main():
    """Example usage of the efficient MMS parser"""

    # Example URL from AEMO SCADA directory
    base_url = "https://www.nemweb.com.au/REPORTS/CURRENT/Dispatch_SCADA/"

    # Use a known file from the directory
    example_file = "PUBLIC_DISPATCHSCADA_202508201545_0000000477140834.zip"
    url = base_url + example_file

    print(f"Downloading {example_file}...")

    parser = AEMOMMSParser()
    csv_content = parser.download_scada_file(url)

    print("Parsing with DuckDB...")
    start = datetime.now()
    tables = parser.parse_mms_csv_efficient(csv_content)
    parse_time = (datetime.now() - start).total_seconds() * 1000

    print(f"\nParsed in {parse_time:.2f} ms")
    print(f"Found {len(tables)} tables:")

    for table_name, df in tables.items():
        print(f"  - {table_name}: {len(df)} rows, {len(df.columns)} columns")
        if len(df) > 0:
            print(f"    Columns: {', '.join(df.columns[:5])}")

    # Example: Query SCADA data directly with SQL
    if "dispatch_unit_scada" in tables:
        print("\nExample SQL query on SCADA data:")
        query = """
            SELECT
                duid,
                AVG(scadavalue) as avg_mw,
                COUNT(*) as reading_count
            FROM dispatch_unit_scada
            GROUP BY duid
            HAVING avg_mw > 0
            ORDER BY avg_mw DESC
            LIMIT 10
        """

        result = parser.parse_with_sql(csv_content, query)
        print(result)

    # Example: Optimized SCADA-specific parsing
    print("\nOptimized SCADA parsing:")
    start = datetime.now()
    scada_df = parser.parse_scada_optimized(csv_content)
    parse_time = (datetime.now() - start).total_seconds() * 1000

    print(f"Parsed SCADA data in {parse_time:.2f} ms")
    print(f"Got {len(scada_df)} SCADA readings")
    if len(scada_df) > 0:
        print("\nFirst 5 SCADA readings:")
        print(scada_df.head())
        print(f"\nUnique DUIDs: {scada_df['duid'].nunique()}")
        print(f"Date range: {scada_df['settlementdate'].min()} to {scada_df['settlementdate'].max()}")

    # Debug: Let's check the header structure
    print("\nDebug - header structure:")
    debug_result = parser.conn.execute("""
        WITH raw_lines AS (
            SELECT
                row_number() OVER () as line_num,
                string_split(line, ',') as parts
            FROM scada_raw_lines
            WHERE trim(line) != ''
        )
        SELECT
            parts[5] as col1,
            parts[6] as col2,
            parts[7] as col3,
            parts[8] as col4
        FROM raw_lines
        WHERE trim(parts[1]) = 'I'
    """).df()
    print("Header columns:")
    print(debug_result)


if __name__ == "__main__":
    main()
