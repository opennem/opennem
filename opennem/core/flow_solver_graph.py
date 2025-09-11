"""
Graph-based Network Flow Solver

A generic flow solver that uses Memgraph to track power flows through an electricity
network, including circular flows and multi-hop emission attribution.

This solver is network-agnostic and can handle any electricity network topology.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from opennem.db.memgraph import get_memgraph_connection

logger = logging.getLogger("opennem.core.flow_solver_graph")


@dataclass
class InterconnectorConfig:
    """Configuration for an interconnector."""

    code: str
    capacity_mw: float | None = None


@dataclass
class FlowSolution:
    """Solution for network flows at a specific interval."""

    interval: datetime
    regional_flows: pd.DataFrame
    circular_flows: list[dict]
    multi_hop_flows: list[dict]
    graph_stats: dict


class GraphFlowSolver:
    """
    Generic graph-based flow solver for electricity networks.

    This solver:
    1. Builds a directed graph of regions and interconnector flows
    2. Detects circular flows (loops) in the network
    3. Tracks multi-hop power flows
    4. Attributes emissions through the network

    Required DataFrame Schemas:

    interconnector_flows:
        - interval: datetime
        - interconnector_code: str
        - network_region_from: str
        - network_region_to: str
        - flow_mw: float (positive or negative, indicating direction)
        - flow_mwh: float (energy for the interval)

    regional_generation:
        - interval: datetime
        - network_region: str
        - generation_mwh: float
        - emissions_t: float (total emissions in tonnes CO2)
        - emission_intensity: float (tCO2/MWh)

    Output regional_flows DataFrame:
        - network_region: str
        - generation_mwh: float
        - local_emissions_t: float
        - imports_mwh: float
        - import_emissions_t: float
        - exports_mwh: float
        - export_emissions_t: float
        - net_position_mwh: float (positive = net importer)
        - net_emissions_t: float
    """

    def __init__(self, interconnectors: list[InterconnectorConfig] | None = None):
        """
        Initialize the solver with optional interconnector configuration.

        Args:
            interconnectors: Optional list of interconnector configurations
        """
        self.interconnectors = {ic.code: ic for ic in interconnectors} if interconnectors else {}
        self.memgraph = get_memgraph_connection()
        self._init_indexes()

    def _init_indexes(self):
        """Initialize Memgraph indexes for performance."""
        try:
            # Create indexes if they don't exist
            self.memgraph.execute_and_commit("CREATE INDEX ON :Region(code)")
            self.memgraph.execute_and_commit("CREATE INDEX ON :Region(interval)")
            self.memgraph.execute_and_commit("CREATE INDEX ON :Region(code, interval)")
        except Exception:
            # Indexes may already exist
            pass

    def solve(self, interval: datetime, interconnector_flows: pd.DataFrame, regional_generation: pd.DataFrame) -> FlowSolution:
        """
        Solve network flows for a specific interval.

        Args:
            interval: The interval to solve for
            interconnector_flows: DataFrame with interconnector flow data
            regional_generation: DataFrame with regional generation and emissions

        Returns:
            FlowSolution containing regional flows, circular flows, and statistics
        """
        # Filter data for the interval
        interval_flows = interconnector_flows[interconnector_flows["interval"] == interval]
        interval_regions = regional_generation[regional_generation["interval"] == interval]

        # Build graph
        stats = self._build_graph(interval, interval_flows, interval_regions)

        # Calculate flows
        regional_flows = self._calculate_regional_flows(interval)
        circular_flows = self._detect_circular_flows(interval)
        multi_hop_flows = self._trace_multi_hop_flows(interval)

        # Create solution
        solution = FlowSolution(
            interval=interval,
            regional_flows=regional_flows,
            circular_flows=circular_flows,
            multi_hop_flows=multi_hop_flows,
            graph_stats=stats,
        )

        return solution

    def _build_graph(self, interval: datetime, flows: pd.DataFrame, regions: pd.DataFrame) -> dict:
        """Build the flow graph in Memgraph."""
        # Clear existing data for this interval
        self.memgraph.execute_and_commit(
            "MATCH (n:Region {interval: $interval}) DETACH DELETE n", {"interval": interval.isoformat()}
        )

        stats = {
            "interval": interval,
            "regions_count": len(regions),
            "flows_count": len(flows),
            "total_generation_mwh": regions["generation_mwh"].sum(),
            "total_emissions_t": regions["emissions_t"].sum(),
        }

        # Create region nodes
        for _, row in regions.iterrows():
            self.memgraph.execute_and_commit(
                """
                CREATE (r:Region {
                    code: $code,
                    interval: $interval,
                    generation_mwh: $generation,
                    emissions_t: $emissions,
                    emission_intensity: $intensity
                })
            """,
                {
                    "code": row["network_region"],
                    "interval": interval.isoformat(),
                    "generation": float(row["generation_mwh"]),
                    "emissions": float(row["emissions_t"]),
                    "intensity": float(row["emission_intensity"]),
                },
            )

        # Create flow edges
        for _, row in flows.iterrows():
            ic_code = row["interconnector_code"]
            flow_mw = row["flow_mw"]
            flow_mwh = row["flow_mwh"]

            # Get regions from dataframe
            if "network_region_from" not in row or "network_region_to" not in row:
                logger.error(f"Missing network_region_from/to for interconnector {ic_code}")
                continue

            from_region = row["network_region_from"]
            to_region = row["network_region_to"]

            # Handle flow direction based on sign
            if flow_mw < 0:
                # Negative flow means reverse direction
                from_region, to_region = to_region, from_region
                flow_mw = abs(flow_mw)
                flow_mwh = abs(flow_mwh)

            # Get actual emissions from source region
            source_emissions = regions[regions["network_region"] == from_region]
            if not source_emissions.empty:
                emission_intensity = source_emissions.iloc[0]["emission_intensity"]
                flow_emissions = flow_mwh * emission_intensity
            else:
                # No emissions if source region not found
                logger.warning(f"No emissions data for region {from_region}")
                flow_emissions = 0

            delivered_mwh = flow_mwh

            self.memgraph.execute_and_commit(
                """
                MATCH (from:Region {code: $from, interval: $interval})
                MATCH (to:Region {code: $to, interval: $interval})
                CREATE (from)-[:FLOWS_TO {
                    interconnector: $interconnector,
                    mw: $mw,
                    mwh_gross: $mwh_gross,
                    mwh_delivered: $mwh_delivered,
                    emissions_t: $emissions
                }]->(to)
            """,
                {
                    "from": from_region,
                    "to": to_region,
                    "interval": interval.isoformat(),
                    "interconnector": ic_code,
                    "mw": abs(flow_mw),
                    "mwh_gross": abs(flow_mwh),
                    "mwh_delivered": delivered_mwh,
                    "emissions": flow_emissions,
                },
            )

        logger.info(f"Built graph for {interval}: {stats}")
        return stats

    def _calculate_regional_flows(self, interval: datetime) -> pd.DataFrame:
        """Calculate imports, exports and net position for each region."""
        # Get all regions
        regions = self.memgraph.execute(
            """
            MATCH (r:Region {interval: $interval})
            RETURN r.code as region,
                   r.generation_mwh as generation,
                   r.emissions_t as emissions
            ORDER BY r.code
            """,
            {"interval": interval.isoformat()},
        )

        results = []
        for row in regions:
            region_code = row[0]
            generation = row[1] or 0
            local_emissions = row[2] or 0

            # Get imports
            imports = self.memgraph.execute(
                """
                MATCH (other:Region)-[f:FLOWS_TO]->(r:Region {code: $region, interval: $interval})
                RETURN sum(f.mwh_delivered) as total_imports,
                       sum(f.emissions_t) as import_emissions
                """,
                {"region": region_code, "interval": interval.isoformat()},
            )

            # Get exports
            exports = self.memgraph.execute(
                """
                MATCH (r:Region {code: $region, interval: $interval})-[f:FLOWS_TO]->(other:Region)
                RETURN sum(f.mwh_gross) as total_exports,
                       sum(f.emissions_t) as export_emissions
                """,
                {"region": region_code, "interval": interval.isoformat()},
            )

            import_data = imports[0] if imports else (0, 0)
            export_data = exports[0] if exports else (0, 0)

            imports_mwh = import_data[0] or 0
            import_emissions = import_data[1] or 0
            exports_mwh = export_data[0] or 0
            export_emissions = export_data[1] or 0

            results.append(
                {
                    "network_region": region_code,
                    "generation_mwh": generation,
                    "local_emissions_t": local_emissions,
                    "imports_mwh": imports_mwh,
                    "import_emissions_t": import_emissions,
                    "exports_mwh": exports_mwh,
                    "export_emissions_t": export_emissions,
                    "net_position_mwh": imports_mwh - exports_mwh,
                    "net_emissions_t": local_emissions + import_emissions - export_emissions,
                }
            )

        return pd.DataFrame(results)

    def _detect_circular_flows(self, interval: datetime, max_loop_length: int = 5) -> list[dict]:
        """Detect circular flows (loops) in the network."""
        results = self.memgraph.execute(
            f"""
            MATCH path = (start:Region {{interval: $interval}})-[:FLOWS_TO*2..{max_loop_length}]->(start)
            WITH start, path, relationships(path) as flows
            WHERE all(f IN flows WHERE f.mwh_delivered > 0.01)
            RETURN DISTINCT
                start.code as start_region,
                [n IN nodes(path) | n.code] as loop_path,
                [f IN flows | {{
                    interconnector: f.interconnector,
                    mwh: f.mwh_delivered,
                    emissions_t: f.emissions_t
                }}] as flows,
                reduce(min_flow = 999999, f IN flows |
                    CASE WHEN f.mwh_delivered < min_flow
                    THEN f.mwh_delivered ELSE min_flow END) as bottleneck_mwh,
                reduce(total = 0, f IN flows | total + f.emissions_t) as total_emissions_t
            LIMIT 100
            """,
            {"interval": interval.isoformat()},
        )

        circular_flows = []
        for row in results:
            circular_flows.append(
                {
                    "start_region": row[0],
                    "loop_path": row[1],
                    "flows": row[2],
                    "bottleneck_mwh": row[3],
                    "total_emissions_t": row[4],
                    "loop_length": len(row[1]) - 1,  # Exclude duplicate start node
                }
            )

        return circular_flows

    def _trace_multi_hop_flows(self, interval: datetime, max_hops: int = 4) -> list[dict]:
        """Trace power flows that traverse multiple regions."""
        results = self.memgraph.execute(
            f"""
            MATCH path = (source:Region {{interval: $interval}})-[:FLOWS_TO*2..{max_hops}]->
                        (dest:Region {{interval: $interval}})
            WHERE source.code <> dest.code
            WITH source, dest, path, relationships(path) as flows, nodes(path) as node_path
            WHERE all(f IN flows WHERE f.mwh_delivered > 0.01)
            RETURN
                source.code as from_region,
                dest.code as to_region,
                [n IN node_path | n.code] as path,
                [f IN flows | {{
                    interconnector: f.interconnector,
                    mwh: f.mwh_delivered,
                    emissions_t: f.emissions_t
                }}] as flow_details,
                reduce(min_flow = 999999, f IN flows |
                    CASE WHEN f.mwh_delivered < min_flow
                    THEN f.mwh_delivered ELSE min_flow END) as bottleneck_mwh,
                reduce(total = 0, f IN flows | total + f.emissions_t) as total_emissions_t,
                size(flows) as hop_count
            ORDER BY bottleneck_mwh DESC
            LIMIT 200
            """,
            {"interval": interval.isoformat()},
        )

        multi_hop = []
        for row in results:
            multi_hop.append(
                {
                    "from_region": row[0],
                    "to_region": row[1],
                    "path": row[2],
                    "flows": row[3],
                    "bottleneck_mwh": row[4],
                    "total_emissions_t": row[5],
                    "hop_count": row[6],
                }
            )

        return multi_hop

    def query_interval(self, interval: datetime) -> FlowSolution | None:
        """
        Query an existing interval from the graph database.

        Args:
            interval: The interval to query

        Returns:
            FlowSolution if the interval exists, None otherwise
        """
        # Check if interval exists
        result = self.memgraph.execute(
            "MATCH (r:Region {interval: $interval}) RETURN count(r) as count", {"interval": interval.isoformat()}
        )

        if not result or result[0][0] == 0:
            return None

        # Get flows from graph
        regional_flows = self._calculate_regional_flows(interval)
        circular_flows = self._detect_circular_flows(interval)
        multi_hop_flows = self._trace_multi_hop_flows(interval)

        # Get stats
        stats_result = self.memgraph.execute(
            """
            MATCH (r:Region {interval: $interval})
            OPTIONAL MATCH ()-[f:FLOWS_TO {interval: $interval}]-()
            RETURN count(DISTINCT r) as regions_count,
                   count(DISTINCT f) as flows_count,
                   sum(r.generation_mwh) as total_generation,
                   sum(r.emissions_t) as total_emissions
            """,
            {"interval": interval.isoformat()},
        )

        if stats_result:
            stats = {
                "interval": interval,
                "regions_count": stats_result[0][0] or 0,
                "flows_count": stats_result[0][1] or 0,
                "total_generation_mwh": stats_result[0][2] or 0,
                "total_emissions_t": stats_result[0][3] or 0,
            }
        else:
            stats = {}

        return FlowSolution(
            interval=interval,
            regional_flows=regional_flows,
            circular_flows=circular_flows,
            multi_hop_flows=multi_hop_flows,
            graph_stats=stats,
        )

    def clear_interval(self, interval: datetime):
        """Clear all data for a specific interval."""
        self.memgraph.execute_and_commit(
            "MATCH (n:Region {interval: $interval}) DETACH DELETE n", {"interval": interval.isoformat()}
        )

    def add_flow(
        self,
        interval: datetime,
        from_region: str,
        to_region: str,
        interconnector_code: str,
        flow_mw: float,
        flow_emissions_t: float,
    ) -> bool:
        """
        Add a flow to the graph.

        Args:
            interval: The interval for the flow
            from_region: Source region code
            to_region: Destination region code
            interconnector_code: Interconnector identifier
            flow_mw: Power flow in MW
            flow_emissions_t: Emissions for this flow in tonnes CO2

        Returns:
            True if successful, False otherwise
        """
        flow_mwh = abs(flow_mw) / 12  # 5-minute interval

        try:
            self.memgraph.execute_and_commit(
                """
                MATCH (from:Region {code: $from, interval: $interval})
                MATCH (to:Region {code: $to, interval: $interval})
                CREATE (from)-[:FLOWS_TO {
                    interconnector: $interconnector,
                    mw: $mw,
                    mwh_gross: $mwh,
                    mwh_delivered: $mwh,
                    emissions_t: $emissions
                }]->(to)
                """,
                {
                    "from": from_region,
                    "to": to_region,
                    "interval": interval.isoformat(),
                    "interconnector": interconnector_code,
                    "mw": abs(flow_mw),
                    "mwh": flow_mwh,
                    "emissions": flow_emissions_t,
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add simulated flow: {e}")
            return False

    def remove_flows_by_interconnector(self, interval: datetime, interconnector_code: str):
        """Remove flows for a specific interconnector at an interval."""
        self.memgraph.execute_and_commit(
            """
            MATCH ()-[f:FLOWS_TO {interconnector: $interconnector}]-()
            WHERE f.interval = $interval
            DELETE f
            """,
            {"interval": interval.isoformat(), "interconnector": interconnector_code},
        )
