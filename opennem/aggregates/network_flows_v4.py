"""
Network Flows v4 - Data Pipeline

This module handles data retrieval and aggregation for network flows:
1. Loads interconnector flows from PostgreSQL
2. Loads regional generation and emissions from ClickHouse
3. Uses GraphFlowSolver to calculate flows
4. Prepares data for storage back to ClickHouse
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from opennem.core.flow_solver_graph import FlowSolution, GraphFlowSolver, InterconnectorConfig
from opennem.db import db_connect_sync
from opennem.db.clickhouse import get_clickhouse_client
from opennem.schema.network import NetworkNEM, NetworkSchema

logger = logging.getLogger("opennem.aggregates.network_flows_v4")


class NetworkFlowsV4:
    """
    Data pipeline for network flows using graph-based solver.
    """

    def __init__(self, network: NetworkSchema = NetworkNEM):
        """Initialize the flow processor."""
        self.network = network
        self.postgres_engine = db_connect_sync()
        self.clickhouse = get_clickhouse_client()

        # Load interconnector configuration
        self.interconnectors = self._load_interconnector_config()

        # Initialize solver
        self.solver = GraphFlowSolver(self.interconnectors)

    def _load_interconnector_config(self) -> list[InterconnectorConfig]:
        """Load interconnector configuration from database."""
        query = f"""
            SELECT DISTINCT
                u.code as interconnector_code,
                u.capacity_registered as capacity_mw
            FROM units u
            JOIN facilities f ON u.station_id = f.id
            WHERE u.interconnector = true
            AND f.network_id = '{self.network.code}'
            ORDER BY u.code
        """

        df = pd.read_sql(query, self.postgres_engine)

        interconnectors = []
        for _, row in df.iterrows():
            interconnectors.append(InterconnectorConfig(code=row["interconnector_code"], capacity_mw=row["capacity_mw"]))

        logger.info(f"Loaded {len(interconnectors)} interconnector configurations")
        return interconnectors

    def load_interconnector_flows(self, start_interval: datetime, end_interval: datetime) -> pd.DataFrame:
        """
        Load interconnector flows from PostgreSQL facility_scada.

        Returns DataFrame with columns:
        - interval: datetime
        - interconnector_code: str
        - network_region_from: str
        - network_region_to: str
        - flow_mw: float (signed, negative indicates reverse flow)
        - flow_mwh: float (always positive, calculated from generated/12)
        """
        query = f"""
            SELECT
                fs.interval,
                u.code as interconnector_code,
                u.interconnector_region_from as network_region_from,
                u.interconnector_region_to as network_region_to,
                fs.generated as flow_mw,
                fs.generated / 12 as flow_mwh  -- ALWAYS use generated/12
            FROM facility_scada fs
            JOIN units u ON fs.facility_code = u.code
            JOIN facilities f ON u.station_id = f.id
            WHERE fs.interval >= '{start_interval}'
            AND fs.interval <= '{end_interval}'
            AND u.interconnector = true
            AND f.network_id = '{self.network.code}'
            AND fs.generated IS NOT NULL
            ORDER BY fs.interval, u.code
        """

        df = pd.read_sql(query, self.postgres_engine)
        logger.info(f"Loaded {len(df)} interconnector flow records")
        return df

    def load_regional_generation(self, start_interval: datetime, end_interval: datetime) -> pd.DataFrame:
        """
        Load regional generation and emissions from ClickHouse unit_intervals.

        Returns DataFrame with columns:
        - interval: datetime
        - network_region: str
        - generation_mwh: float
        - emissions_t: float
        - emission_intensity: float (tCO2/MWh)
        """
        query = """
            SELECT
                interval,
                network_region,
                sum(energy) as generation_mwh,
                sum(emissions) as emissions_t,
                sum(emissions) / nullif(sum(energy), 0) as emission_intensity
            FROM unit_intervals
            WHERE network_id = %(network_id)s
            AND interval >= %(start)s
            AND interval <= %(end)s
            AND energy > 0
            GROUP BY interval, network_region
            ORDER BY interval, network_region
        """

        params = {"network_id": self.network.code, "start": start_interval, "end": end_interval}

        result = self.clickhouse.execute(query, params)

        # Convert to DataFrame
        df = pd.DataFrame(result, columns=["interval", "network_region", "generation_mwh", "emissions_t", "emission_intensity"])

        # Fill nulls
        df["generation_mwh"] = df["generation_mwh"].fillna(0)
        df["emissions_t"] = df["emissions_t"].fillna(0)
        df["emission_intensity"] = df["emission_intensity"].fillna(0.7)  # Default

        logger.info(f"Loaded {len(df)} regional generation records")
        return df

    def process_interval(self, interval: datetime) -> FlowSolution:
        """
        Process flows for a single interval.

        Args:
            interval: The interval to process

        Returns:
            FlowSolution containing calculated flows
        """
        # Load data for the interval
        flows = self.load_interconnector_flows(interval, interval)
        generation = self.load_regional_generation(interval, interval)

        # Solve flows
        solution = self.solver.solve(interval, flows, generation)

        return solution

    def process_interval_range(
        self, start_interval: datetime, end_interval: datetime, batch_size_hours: int = 24
    ) -> list[FlowSolution]:
        """
        Process a range of intervals in batches.

        Args:
            start_interval: Start of the range
            end_interval: End of the range
            batch_size_hours: Size of each batch in hours

        Returns:
            List of FlowSolutions for each interval
        """
        solutions = []
        current = start_interval

        while current <= end_interval:
            batch_end = min(current + timedelta(hours=batch_size_hours), end_interval)

            logger.info(f"Processing batch: {current} to {batch_end}")

            # Load data for batch
            flows = self.load_interconnector_flows(current, batch_end)
            generation = self.load_regional_generation(current, batch_end)

            # Get unique intervals
            intervals = sorted(set(flows["interval"].unique()) | set(generation["interval"].unique()))

            # Process each interval
            for interval in intervals:
                if current <= interval <= batch_end:
                    try:
                        solution = self.solver.solve(interval, flows, generation)
                        solutions.append(solution)
                        logger.debug(f"Processed interval {interval}")
                    except Exception as e:
                        logger.error(f"Failed to process interval {interval}: {e}")

            current = batch_end + timedelta(minutes=5)

        logger.info(f"Processed {len(solutions)} intervals total")
        return solutions

    def prepare_for_clickhouse(self, solutions: list[FlowSolution]) -> pd.DataFrame:
        """
        Prepare solutions for storage in ClickHouse.

        Creates a DataFrame suitable for insertion into a ClickHouse table
        with network flow data.
        """
        records = []

        for solution in solutions:
            for _, row in solution.regional_flows.iterrows():
                records.append(
                    {
                        "interval": solution.interval,
                        "network_id": self.network.code,
                        "network_region": row["network_region"],
                        "generation_mwh": row["generation_mwh"],
                        "local_emissions_t": row["local_emissions_t"],
                        "imports_mwh": row["imports_mwh"],
                        "import_emissions_t": row["import_emissions_t"],
                        "exports_mwh": row["exports_mwh"],
                        "export_emissions_t": row["export_emissions_t"],
                        "net_position_mwh": row["net_position_mwh"],
                        "net_emissions_t": row["net_emissions_t"],
                        "circular_flows_count": len(solution.circular_flows),
                        "multi_hop_flows_count": len(solution.multi_hop_flows),
                    }
                )

        return pd.DataFrame(records)

    def get_flow_summary(self, interval: datetime) -> dict:
        """
        Get a complete summary of flows for an interval.

        Returns:
            Dictionary with regional flows, circular flows, and statistics
        """
        # Try to query existing data first
        existing = self.solver.query_interval(interval)
        if existing:
            return {
                "interval": interval,
                "regional_flows": existing.regional_flows.to_dict("records"),
                "circular_flows": existing.circular_flows,
                "multi_hop_flows": existing.multi_hop_flows,
                "stats": existing.graph_stats,
            }

        # Process the interval if not found
        solution = self.process_interval(interval)

        return {
            "interval": interval,
            "regional_flows": solution.regional_flows.to_dict("records"),
            "circular_flows": solution.circular_flows,
            "multi_hop_flows": solution.multi_hop_flows,
            "stats": solution.graph_stats,
        }

    def test_nsw_sa_interconnector(self, interval: datetime) -> dict:
        """
        Test the impact of adding NSW-SA interconnector.

        Returns:
            Dictionary with before/after comparison
        """
        # Get current state
        before = self.solver.query_interval(interval)
        if not before:
            before = self.process_interval(interval)

        # Calculate emissions based on NSW1 emission intensity
        regional_gen = self.load_regional_generation(interval, interval)
        nsw_data = regional_gen[regional_gen["network_region"] == "NSW1"]
        if not nsw_data.empty:
            emission_intensity = nsw_data.iloc[0]["emission_intensity"]
            flow_emissions = (300 / 12) * emission_intensity  # 300 MW for 5 minutes
        else:
            flow_emissions = 0

        # Add test interconnector flow
        success = self.solver.add_flow(interval, "NSW1", "SA1", "NSW1-SA1 (TEST)", 300, flow_emissions)

        if not success:
            return {"error": "Failed to add test interconnector"}

        # Get new state
        after = self.solver.query_interval(interval)

        # Clean up
        self.solver.remove_flows_by_interconnector(interval, "NSW1-SA1 (TEST)")

        return {
            "before": {"circular_flows_count": len(before.circular_flows), "multi_hop_flows_count": len(before.multi_hop_flows)},
            "after": {
                "circular_flows_count": len(after.circular_flows),
                "multi_hop_flows_count": len(after.multi_hop_flows),
                "new_circular_flows": len(after.circular_flows) - len(before.circular_flows),
                "new_multi_hop_flows": len(after.multi_hop_flows) - len(before.multi_hop_flows),
            },
        }
