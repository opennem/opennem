"""Flow solver v4 — dynamic topology, polars-based.

Computes per-region energy imports/exports and flow emissions using interconnector
SCADA data and regional emissions intensities.

Two modes:
- simple (default): emissions on flow A->B = energy(A->B) * generation_intensity(A)
  This matches v3 behaviour and is suitable for tree topologies.
- consumption_mix: solves a linear system accounting for transit flows through
  intermediate regions. Required for accurate accounting with loops (e.g. PEC).
"""

import logging

import numpy as np
import polars as pl

from opennem.core.interconnector_topology import NetworkTopology

logger = logging.getLogger("opennem.core.flow_solver_v4")


def compute_region_flows(
    topology: NetworkTopology,
    interconnector_df: pl.DataFrame,
) -> pl.DataFrame:
    """Compute per-region energy imports and exports from interconnector data.

    Args:
        topology: network topology
        interconnector_df: DataFrame with columns:
            interval, interconnector_region_from, interconnector_region_to, energy (MWh)
            Energy is signed: positive = flow in declared direction.

    Returns:
        DataFrame with columns: interval, network_region, energy_imports, energy_exports
        All values are non-negative MWh.
    """
    if interconnector_df.is_empty():
        return pl.DataFrame(
            schema={
                "interval": pl.Datetime,
                "network_region": pl.String,
                "energy_imports": pl.Float64,
                "energy_exports": pl.Float64,
            }
        )

    df = interconnector_df.clone()

    # Normalize flows: when energy < 0, flip direction
    flipped = (
        df.filter(pl.col("energy") < 0)
        .with_columns(
            pl.col("interconnector_region_from").alias("_to"),
            pl.col("interconnector_region_to").alias("_from"),
            (pl.col("energy").abs()).alias("energy"),
        )
        .select(
            pl.col("interval"),
            pl.col("_from").alias("interconnector_region_from"),
            pl.col("_to").alias("interconnector_region_to"),
            pl.col("energy"),
        )
    )

    positive = df.filter(pl.col("energy") >= 0)
    normalized = pl.concat([positive, flipped])

    # Exports: sum energy grouped by (interval, region_from)
    exports = (
        normalized.group_by(["interval", "interconnector_region_from"])
        .agg(pl.col("energy").sum().alias("energy_exports"))
        .rename({"interconnector_region_from": "network_region"})
    )

    # Imports: sum energy grouped by (interval, region_to)
    imports = (
        normalized.group_by(["interval", "interconnector_region_to"])
        .agg(pl.col("energy").sum().alias("energy_imports"))
        .rename({"interconnector_region_to": "network_region"})
    )

    # Merge
    result = exports.join(imports, on=["interval", "network_region"], how="full", coalesce=True).with_columns(
        pl.col("energy_imports").fill_null(0.0),
        pl.col("energy_exports").fill_null(0.0),
    )

    return result.sort(["interval", "network_region"])


def solve_flow_emissions_simple(
    topology: NetworkTopology,
    interconnector_df: pl.DataFrame,
    region_emissions_df: pl.DataFrame,
) -> pl.DataFrame:
    """Simple emissions allocation: flow emissions = flow energy * source region intensity.

    Matches v3 behaviour. Does not account for transit flows.

    Args:
        topology: network topology
        interconnector_df: columns: interval, interconnector_region_from, interconnector_region_to, energy
        region_emissions_df: columns: interval, network_region, energy (MWh), emissions (t), emissions_intensity

    Returns:
        DataFrame: interval, network_region, energy_imports, energy_exports,
                   emissions_imports, emissions_exports
    """
    if interconnector_df.is_empty():
        return _empty_result()

    df = interconnector_df.clone()

    # Normalize flows (flip negative)
    flipped = (
        df.filter(pl.col("energy") < 0)
        .with_columns(
            pl.col("interconnector_region_from").alias("_to"),
            pl.col("interconnector_region_to").alias("_from"),
            (pl.col("energy").abs()).alias("energy"),
        )
        .select(
            pl.col("interval"),
            pl.col("_from").alias("interconnector_region_from"),
            pl.col("_to").alias("interconnector_region_to"),
            pl.col("energy"),
        )
    )
    positive = df.filter(pl.col("energy") >= 0)
    normalized = pl.concat([positive, flipped])

    # Join with source region intensity to compute per-flow emissions
    intensities = region_emissions_df.select("interval", "network_region", "emissions_intensity")

    with_emissions = normalized.join(
        intensities,
        left_on=["interval", "interconnector_region_from"],
        right_on=["interval", "network_region"],
        how="left",
    ).with_columns(
        (pl.col("energy") * pl.col("emissions_intensity").fill_null(0.0)).alias("emissions"),
    )

    # Aggregate imports per region
    imports = (
        with_emissions.group_by(["interval", "interconnector_region_to"])
        .agg(
            pl.col("energy").sum().alias("energy_imports"),
            pl.col("emissions").sum().alias("emissions_imports"),
        )
        .rename({"interconnector_region_to": "network_region"})
    )

    # Aggregate exports per region
    exports = (
        with_emissions.group_by(["interval", "interconnector_region_from"])
        .agg(
            pl.col("energy").sum().alias("energy_exports"),
            pl.col("emissions").sum().alias("emissions_exports"),
        )
        .rename({"interconnector_region_from": "network_region"})
    )

    result = exports.join(imports, on=["interval", "network_region"], how="full", coalesce=True).with_columns(
        pl.col("energy_imports").fill_null(0.0),
        pl.col("energy_exports").fill_null(0.0),
        pl.col("emissions_imports").fill_null(0.0),
        pl.col("emissions_exports").fill_null(0.0),
    )

    return result.sort(["interval", "network_region"])


def solve_flow_emissions_consumption_mix(
    topology: NetworkTopology,
    interconnector_df: pl.DataFrame,
    region_emissions_df: pl.DataFrame,
) -> pl.DataFrame:
    """Consumption-mix emissions: accounts for transit flows through intermediate regions.

    For each region r, solves for consumption_intensity(r) such that:
        consumption_intensity(r) * total_supply(r) =
            local_emissions(r) + sum(flow(x->r) * consumption_intensity(x))

    where total_supply(r) = local_energy(r) + sum(flow(x->r))

    Uses numpy.linalg.lstsq for loop-safe solving.

    Returns same schema as solve_flow_emissions_simple.
    """
    if interconnector_df.is_empty():
        return _empty_result()

    # Normalize flows
    df = interconnector_df.clone()
    flipped = (
        df.filter(pl.col("energy") < 0)
        .with_columns(
            pl.col("interconnector_region_from").alias("_to"),
            pl.col("interconnector_region_to").alias("_from"),
            (pl.col("energy").abs()).alias("energy"),
        )
        .select(
            pl.col("interval"),
            pl.col("_from").alias("interconnector_region_from"),
            pl.col("_to").alias("interconnector_region_to"),
            pl.col("energy"),
        )
    )
    positive = df.filter(pl.col("energy") >= 0)
    normalized = pl.concat([positive, flipped])

    intervals = sorted(region_emissions_df["interval"].unique().to_list())
    regions = list(topology.regions)
    n = len(regions)
    region_idx = {r: i for i, r in enumerate(regions)}

    all_results: list[dict] = []

    for interval in intervals:
        # Get regional data for this interval
        region_data = region_emissions_df.filter(pl.col("interval") == interval)
        flow_data = normalized.filter(pl.col("interval") == interval)

        # Build local emissions and energy vectors
        local_emissions = np.zeros(n)
        local_energy = np.zeros(n)
        for row in region_data.iter_rows(named=True):
            idx = region_idx.get(row["network_region"])
            if idx is not None:
                local_energy[idx] = row.get("energy", 0.0) or 0.0
                local_emissions[idx] = row.get("emissions", 0.0) or 0.0

        # Build flow matrix: flow_matrix[i][j] = energy flowing from region i to region j
        flow_matrix = np.zeros((n, n))
        for row in flow_data.iter_rows(named=True):
            fi = region_idx.get(row["interconnector_region_from"])
            ti = region_idx.get(row["interconnector_region_to"])
            if fi is not None and ti is not None:
                flow_matrix[fi][ti] += row["energy"] or 0.0

        # Total supply per region = local generation + imports
        total_imports = flow_matrix.sum(axis=0)  # sum of column = imports into region
        total_supply = local_energy + total_imports

        # Build linear system: A * intensity = b
        # For each region r: total_supply[r] * intensity[r] - sum(flow[x->r] * intensity[x]) = local_emissions[r]
        a_matrix = np.diag(total_supply) - flow_matrix.T  # flow_matrix.T[r][x] = flow from x to r
        b_vector = local_emissions

        # Solve
        try:
            intensities, _, _, _ = np.linalg.lstsq(a_matrix, b_vector, rcond=None)
        except np.linalg.LinAlgError:
            logger.warning(f"lstsq failed for interval {interval}, falling back to simple intensity")
            intensities = np.where(local_energy > 0, local_emissions / local_energy, 0.0)

        # Clamp negative intensities to 0
        intensities = np.maximum(intensities, 0.0)

        # Compute per-region imports/exports/emissions using consumption-mix intensities
        total_exports = flow_matrix.sum(axis=1)  # sum of row = exports from region

        for i, region in enumerate(regions):
            import_energy = total_imports[i]
            export_energy = total_exports[i]

            # Import emissions: sum of flow(x->r) * intensity(x)
            import_emissions = sum(flow_matrix[x][i] * intensities[x] for x in range(n))

            # Export emissions: exports from r carry r's consumption-mix intensity
            export_emissions = export_energy * intensities[i]

            all_results.append(
                {
                    "interval": interval,
                    "network_region": region,
                    "energy_imports": float(import_energy),
                    "energy_exports": float(export_energy),
                    "emissions_imports": float(import_emissions),
                    "emissions_exports": float(export_emissions),
                }
            )

    return pl.DataFrame(all_results).sort(["interval", "network_region"])


def solve_flows_v4(
    topology: NetworkTopology,
    interconnector_df: pl.DataFrame,
    region_emissions_df: pl.DataFrame,
    use_consumption_mix: bool = False,
) -> pl.DataFrame:
    """Main entry point for v4 flow solver.

    Args:
        topology: network topology
        interconnector_df: columns: interval, interconnector_region_from, interconnector_region_to, energy (MWh)
        region_emissions_df: columns: interval, network_region, energy, emissions, emissions_intensity
        use_consumption_mix: if True, use consumption-mix method (loop-aware)

    Returns:
        DataFrame: interval, network_region, energy_imports, energy_exports,
                   emissions_imports, emissions_exports
    """
    if use_consumption_mix:
        return solve_flow_emissions_consumption_mix(topology, interconnector_df, region_emissions_df)
    return solve_flow_emissions_simple(topology, interconnector_df, region_emissions_df)


def _empty_result() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "interval": pl.Datetime,
            "network_region": pl.String,
            "energy_imports": pl.Float64,
            "energy_exports": pl.Float64,
            "emissions_imports": pl.Float64,
            "emissions_exports": pl.Float64,
        }
    )
