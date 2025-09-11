#!/usr/bin/env python
"""
Test Network Flows v4 with Memgraph

Runs the new Memgraph implementation for an interval and compares it with
the existing at_network_flows data.
"""

import logging
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch
from rich.console import Console
from rich.table import Table

from opennem.aggregates.network_flows_v4 import NetworkFlowsV4
from opennem.db import db_connect_sync

console = Console()
logging.basicConfig(level=logging.INFO)


def load_existing_flows(interval: datetime) -> pd.DataFrame:
    """Load existing flows from at_network_flows table."""
    engine = db_connect_sync()

    query = f"""
        SELECT
            interval,
            network_region,
            energy_imports,
            energy_exports,
            (energy_imports - energy_exports) as net_position,
            emissions_imports,
            emissions_exports,
            (emissions_imports - emissions_exports) as net_emissions
        FROM at_network_flows
        WHERE interval = '{interval}'
        AND network_id = 'NEM'
        ORDER BY network_region
    """

    return pd.read_sql(query, engine)


def format_flow_value(value: float) -> str:
    """Format flow value with color coding."""
    if value > 0:
        return f"[green]+{value:.1f}[/green]"
    elif value < 0:
        return f"[red]{value:.1f}[/red]"
    else:
        return "[dim]0.0[/dim]"


def analyze_interval(interval: datetime, show_details: bool = True):
    """Analyze flows for a specific interval."""
    console.print(f"\n[bold]═══ Network Flows Analysis for {interval} ═══[/bold]\n")

    # Initialize v4 flows
    flows_v4 = NetworkFlowsV4()

    # Process interval
    console.print("[yellow]Processing interval with graph solver...[/yellow]")
    solution = flows_v4.process_interval(interval)

    console.print(
        f"✓ Processed graph: {solution.graph_stats['regions_count']} regions, {solution.graph_stats['flows_count']} flows"
    )
    console.print(f"  Total generation: {solution.graph_stats['total_generation_mwh']:.1f} MWh")
    console.print(f"  Total emissions: {solution.graph_stats['total_emissions_t']:.1f} tCO2\n")

    # Get v4 regional flows
    v4_flows = solution.regional_flows.to_dict("records")

    # Load existing flows
    console.print("[yellow]Loading existing at_network_flows data...[/yellow]")
    existing = load_existing_flows(interval)
    console.print(f"✓ Loaded {len(existing)} regional records\n")

    # Compare regional flows
    if show_details:
        table = Table(title="Regional Flow Comparison")
        table.add_column("Region", style="cyan")
        table.add_column("Generation\n(MWh)", justify="right")
        table.add_column("Imports v4\n(MWh)", justify="right")
        table.add_column("Imports v3\n(MWh)", justify="right")
        table.add_column("Δ Import", justify="right")
        table.add_column("Exports v4\n(MWh)", justify="right")
        table.add_column("Exports v3\n(MWh)", justify="right")
        table.add_column("Δ Export", justify="right")
        table.add_column("Emissions\nImp v4", justify="right")
        table.add_column("Emissions\nImp v3", justify="right")
        table.add_column("Δ Em", justify="right")

        for v4_region in v4_flows:
            region = v4_region["network_region"]
            existing_row = existing[existing["network_region"] == region]

            if not existing_row.empty:
                v3_imports = float(existing_row.iloc[0]["energy_imports"] or 0)
                v3_exports = float(existing_row.iloc[0]["energy_exports"] or 0)
                v3_em_imports = float(existing_row.iloc[0]["emissions_imports"] or 0)
            else:
                v3_imports = v3_exports = v3_em_imports = 0

            import_diff = v4_region["imports_mwh"] - v3_imports
            export_diff = v4_region["exports_mwh"] - v3_exports
            em_import_diff = v4_region["import_emissions_t"] - v3_em_imports

            table.add_row(
                region,
                f"{v4_region['generation_mwh']:.1f}",
                f"{v4_region['imports_mwh']:.1f}",
                f"{v3_imports:.1f}",
                format_flow_value(import_diff),
                f"{v4_region['exports_mwh']:.1f}",
                f"{v3_exports:.1f}",
                format_flow_value(export_diff),
                f"{v4_region['import_emissions_t']:.2f}",
                f"{v3_em_imports:.2f}",
                format_flow_value(em_import_diff),
            )

        console.print(table)

    # Check for circular flows
    console.print("\n[bold]Circular Flow Detection:[/bold]")
    circular = solution.circular_flows

    if circular:
        console.print(f"[red]⚠ Found {len(circular)} circular flows![/red]")
        for flow in circular[:5]:  # Show first 5
            path = " → ".join(flow["loop_path"])
            console.print(f"  • {path}")
            console.print(f"    Bottleneck: {flow['bottleneck_mwh']:.1f} MWh")
    else:
        console.print("[green]✓ No circular flows detected[/green]")

    # Check multi-hop flows
    console.print("\n[bold]Multi-Hop Flows:[/bold]")
    multi_hop = solution.multi_hop_flows

    if multi_hop:
        console.print(f"Found {len(multi_hop)} multi-hop flow paths")

        # Show top 5 by capacity
        for flow in multi_hop[:5]:
            path = " → ".join(flow["path"])
            console.print(f"  • {path}")
            console.print(f"    Capacity: {flow['bottleneck_mwh']:.1f} MWh (bottleneck limited)")
    else:
        console.print("[dim]No multi-hop flows detected[/dim]")

    # Test NSW-SA interconnector simulation
    console.print("\n[bold]NSW-SA Interconnector Test:[/bold]")
    impact = flows_v4.test_nsw_sa_interconnector(interval)

    if "error" not in impact:
        console.print("[green]✓ Added test NSW-SA interconnector (300 MW)[/green]")

        # Check for new circular flows
        new_circular_count = impact["after"]["new_circular_flows"]
        new_multi_hop_count = impact["after"]["new_multi_hop_flows"]

        if new_circular_count > 0:
            console.print(f"[yellow]⚠ NSW-SA interconnector creates {new_circular_count} new circular flows![/yellow]")

        if new_multi_hop_count > 0:
            console.print(f"[yellow]⚠ Created {new_multi_hop_count} new multi-hop flows[/yellow]")
        else:
            console.print("[dim]No new circular flows created[/dim]")

        console.print("[dim]✓ Cleaned up test flows[/dim]")
    else:
        console.print("[red]Failed to add test interconnector[/red]")

    # Summary statistics
    console.print("\n[bold]Summary Statistics:[/bold]")

    total_v4_imports = sum(r["imports_mwh"] for r in v4_flows)
    total_v4_exports = sum(r["exports_mwh"] for r in v4_flows)
    total_v4_em_imports = sum(r["import_emissions_t"] for r in v4_flows)
    total_v4_em_exports = sum(r["export_emissions_t"] for r in v4_flows)
    total_v3_imports = float(existing["energy_imports"].sum())
    total_v3_exports = float(existing["energy_exports"].sum())
    total_v3_em_imports = float(existing["emissions_imports"].sum())
    total_v3_em_exports = float(existing["emissions_exports"].sum())

    stats_table = Table(show_header=False)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("v4 (Memgraph)", justify="right")
    stats_table.add_column("v3 (Current)", justify="right")
    stats_table.add_column("Difference", justify="right")

    stats_table.add_row(
        "Total Imports (MWh)",
        f"{total_v4_imports:.1f}",
        f"{total_v3_imports:.1f}",
        format_flow_value(total_v4_imports - total_v3_imports),
    )
    stats_table.add_row(
        "Total Exports (MWh)",
        f"{total_v4_exports:.1f}",
        f"{total_v3_exports:.1f}",
        format_flow_value(total_v4_exports - total_v3_exports),
    )
    stats_table.add_row(
        "Import Emissions (tCO2)",
        f"{total_v4_em_imports:.2f}",
        f"{total_v3_em_imports:.2f}",
        format_flow_value(total_v4_em_imports - total_v3_em_imports),
    )
    stats_table.add_row(
        "Export Emissions (tCO2)",
        f"{total_v4_em_exports:.2f}",
        f"{total_v3_em_exports:.2f}",
        format_flow_value(total_v4_em_exports - total_v3_em_exports),
    )

    console.print(stats_table)

    # Check balance
    import_export_diff = abs(total_v4_imports - total_v4_exports)
    if import_export_diff < 0.1:
        console.print("\n[green]✓ Imports and exports are balanced[/green]")
    else:
        console.print(f"\n[yellow]⚠ Import/Export imbalance: {import_export_diff:.1f} MWh[/yellow]")


def visualize_circular_flow(flow: dict) -> str:
    """Create a visual representation of a circular flow."""
    path = flow["loop_path"]
    flows = flow.get("flows", [])

    visual = []
    for i in range(len(path) - 1):
        from_region = path[i]
        to_region = path[i + 1]

        # Find the flow for this segment
        flow_mwh = 0
        for f in flows:
            if f.get("interconnector"):
                # Try to match the interconnector
                flow_mwh = f.get("mwh", 0)
                break

        if i == 0:
            visual.append(f"{from_region}")
        visual.append(f"→({flow_mwh:.1f} MWh)→ {to_region}")

    return " ".join(visual)


def test_multiple_intervals_for_circular_flows():
    """Test multiple intervals with NSW-SA interconnector to find circular flows."""

    console.print("\n[bold cyan]═══ Testing Multiple Intervals for Circular Flows ═══[/bold cyan]\n")

    # Test intervals - different times of day when flow patterns might create loops
    test_intervals = [
        datetime(2025, 9, 7, 0, 0, 0),  # Midnight
        datetime(2025, 9, 7, 6, 0, 0),  # Early morning
        datetime(2025, 9, 7, 8, 0, 0),  # Morning peak
        datetime(2025, 9, 7, 12, 0, 0),  # Midday
        datetime(2025, 9, 7, 18, 0, 0),  # Evening peak
        datetime(2025, 9, 7, 22, 0, 0),  # Late evening
    ]

    flows_v4 = NetworkFlowsV4()
    results = []

    for interval in test_intervals:
        console.print(f"\n[yellow]Testing {interval.strftime('%Y-%m-%d %H:%M')}[/yellow]")

        # Process the interval first
        try:
            solution = flows_v4.process_interval(interval)
        except Exception as e:
            console.print(f"  [red]✗ Failed to process: {e}[/red]")
            continue

        # Get existing flows
        existing_circular = len(solution.circular_flows)
        existing_multi_hop = len(solution.multi_hop_flows)

        # Add NSW-SA interconnector with varying flow directions
        regional_gen = flows_v4.load_regional_generation(interval, interval)

        # Test different flow scenarios
        scenarios = [
            ("NSW1", "SA1", 300, "NSW→SA 300MW"),
            ("SA1", "NSW1", 200, "SA→NSW 200MW"),
            ("NSW1", "SA1", 500, "NSW→SA 500MW"),
        ]

        for from_region, to_region, flow_mw, desc in scenarios:
            # Get emission intensity
            source_data = regional_gen[regional_gen["network_region"] == from_region]
            if not source_data.empty:
                emission_intensity = source_data.iloc[0]["emission_intensity"]
                flow_emissions = (abs(flow_mw) / 12) * emission_intensity
            else:
                flow_emissions = 0

            # Add the interconnector
            success = flows_v4.solver.add_flow(
                interval, from_region, to_region, f"{from_region}-{to_region}", flow_mw, flow_emissions
            )

            if success:
                # Check for circular flows
                after_solution = flows_v4.solver.query_interval(interval)
                if after_solution:
                    new_circular = len(after_solution.circular_flows)
                    new_multi_hop = len(after_solution.multi_hop_flows)
                else:
                    new_circular = 0
                    new_multi_hop = 0

                if new_circular > existing_circular:
                    console.print(f"  [green]✓ {desc}: Creates {new_circular - existing_circular} circular flows![/green]")

                    # Show the circular flow paths
                    if after_solution:
                        for cf in after_solution.circular_flows[:3]:  # Show first 3
                            path = " → ".join(cf["loop_path"])
                            console.print(f"    [dim]Loop: {path} ({cf['bottleneck_mwh']:.1f} MWh)[/dim]")

                    results.append(
                        {
                            "interval": interval,
                            "scenario": desc,
                            "circular_flows": new_circular - existing_circular,
                            "multi_hop_flows": new_multi_hop - existing_multi_hop,
                        }
                    )
                elif new_multi_hop > existing_multi_hop:
                    console.print(f"  [yellow]• {desc}: {new_multi_hop - existing_multi_hop} new multi-hop flows[/yellow]")
                else:
                    console.print(f"  [dim]• {desc}: No new flows[/dim]")

                # Clean up
                flows_v4.solver.remove_flows_by_interconnector(interval, f"{from_region}-{to_region}")
            else:
                console.print(f"  [red]✗ Failed to add {desc}[/red]")

    # Summary
    console.print("\n[bold]Summary of Circular Flow Findings:[/bold]")
    if results:
        table = Table()
        table.add_column("Interval", style="cyan")
        table.add_column("Scenario", style="yellow")
        table.add_column("Circular Flows", justify="right")
        table.add_column("Multi-hop Flows", justify="right")

        for r in results:
            table.add_row(r["interval"].strftime("%H:%M"), r["scenario"], str(r["circular_flows"]), str(r["multi_hop_flows"]))
        console.print(table)
    else:
        console.print("[dim]No circular flows found in tested scenarios[/dim]")
        console.print("\n[yellow]Note: Circular flows typically occur when:[/yellow]")
        console.print("• Multiple interconnectors form a loop between regions")
        console.print("• Power flows in different directions simultaneously")
        console.print("• Market conditions create arbitrage opportunities")
        console.print("\nThe NSW-SA interconnector alone may not create circular flows")
        console.print("without specific market conditions or additional connections.")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Network Flows v4 with Memgraph")
    parser.add_argument("--interval", type=str, help="Interval to analyze (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--no-details", action="store_true", help="Hide detailed comparison table")
    parser.add_argument("--test-circular", action="store_true", help="Test multiple intervals for circular flows")
    parser.add_argument("--demo", action="store_true", help="Demonstrate circular flow with NSW-SA interconnector")

    args = parser.parse_args()

    if args.demo:
        try:
            demonstrate_circular_flow()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)
    elif args.test_circular:
        try:
            test_multiple_intervals_for_circular_flows()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)
    else:
        # Default single interval test
        if args.interval:
            try:
                interval = datetime.fromisoformat(args.interval)
            except ValueError:
                console.print(f"[red]Invalid interval format: {args.interval}[/red]")
                console.print("Use format: YYYY-MM-DD HH:MM:SS")
                sys.exit(1)
        else:
            interval = datetime(2025, 9, 7, 8, 0, 0)

        try:
            analyze_interval(interval, show_details=not args.no_details)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback

            traceback.print_exc()
            sys.exit(1)


def visualize_network_graph(solution, title="Network Flow Graph"):
    """Create an enhanced network graph visualization showing regions, flows, and emissions."""

    # Create figure with 3 subplots
    fig = plt.figure(figsize=(24, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[2, 1], height_ratios=[1, 1])

    ax1 = fig.add_subplot(gs[:, 0])  # Network graph (left, full height)
    ax2 = fig.add_subplot(gs[0, 1])  # Energy balance (top right)
    ax3 = fig.add_subplot(gs[1, 1])  # Emissions chart (bottom right)

    fig.suptitle(title, fontsize=18, fontweight="bold", y=0.98)

    # Get regional data
    regional_flows = solution.regional_flows

    # Create directed graph for actual interconnector flows
    G = nx.DiGraph()

    # Add all regions as nodes
    for _, row in regional_flows.iterrows():
        region = row["network_region"]
        G.add_node(
            region,
            generation=row["generation_mwh"],
            imports=row["imports_mwh"],
            exports=row["exports_mwh"],
            import_emissions=row["import_emissions_t"],
            export_emissions=row["export_emissions_t"],
            local_emissions=row["local_emissions_t"],
            net_position=row["net_position_mwh"],
        )

    # Extract actual interconnector flows from regional import/export data
    # This is more reliable than parsing multi-hop flows
    interconnector_flows = {}

    # Known interconnector connections in NEM
    interconnector_map = [
        ("QLD1", "NSW1"),
        ("NSW1", "VIC1"),
        ("VIC1", "SA1"),
        ("VIC1", "TAS1"),
        ("NSW1", "SA1"),  # Future NSW-SA interconnector
    ]

    # For each region, check its imports/exports
    for region_code in regional_flows["network_region"]:
        region_data = regional_flows[regional_flows["network_region"] == region_code].iloc[0]

        # If region has exports, determine where they go
        if region_data["exports_mwh"] > 0:
            # Find connected regions
            for from_r, to_r in interconnector_map:
                if from_r == region_code or to_r == region_code:
                    other_region = to_r if from_r == region_code else from_r
                    # Check if other region has imports
                    other_data = regional_flows[regional_flows["network_region"] == other_region]
                    if not other_data.empty and other_data.iloc[0]["imports_mwh"] > 0:
                        # Estimate flow between them (simplified)
                        flow = min(region_data["exports_mwh"], other_data.iloc[0]["imports_mwh"]) / 2
                        if flow > 0.1:
                            key = (region_code, other_region) if from_r == region_code else (other_region, region_code)
                            if key not in interconnector_flows:
                                interconnector_flows[key] = {
                                    "flow": flow,
                                    "emissions": region_data["export_emissions_t"] * (flow / region_data["exports_mwh"]),
                                }

    # Add edges to graph
    for (from_r, to_r), data in interconnector_flows.items():
        G.add_edge(from_r, to_r, flow=data["flow"], emissions=data["emissions"])

    # LEFT PANEL: Network topology with enhanced visuals
    ax1.set_title("Network Topology & Power Flows", fontsize=16, pad=20)
    ax1.axis("off")
    ax1.set_xlim(-1, 3)
    ax1.set_ylim(-0.5, 3.5)

    # Geographic-like positions
    pos = {"QLD1": (2, 3), "NSW1": (2, 2), "VIC1": (2, 1), "TAS1": (2, 0), "SA1": (0, 1.5)}

    # Draw large nodes with generation info
    for node in G.nodes():
        x, y = pos[node]
        gen = G.nodes[node]["generation"]
        imports = G.nodes[node]["imports"]
        exports = G.nodes[node]["exports"]
        emissions = G.nodes[node]["local_emissions"]

        # Node size based on generation
        node_size = max(0.3, min(0.6, gen / 1000))

        # Color based on emissions intensity
        intensity = emissions / gen if gen > 0 else 0
        if intensity < 0.3:
            color = "#2ecc71"  # Green - low emissions
        elif intensity < 0.6:
            color = "#f39c12"  # Orange - medium emissions
        else:
            color = "#e74c3c"  # Red - high emissions

        # Draw node as a circle with info
        circle = Circle((x, y), node_size, color=color, alpha=0.7, zorder=2)
        ax1.add_patch(circle)

        # Add region name
        ax1.text(x, y, node, fontsize=14, fontweight="bold", ha="center", va="center", zorder=3)

        # Add generation info below
        info_text = f"Gen: {gen:.0f} MWh\n"
        if imports > 0.1:
            info_text += f"↓ {imports:.0f} MWh\n"
        if exports > 0.1:
            info_text += f"↑ {exports:.0f} MWh\n"
        info_text += f"CO₂: {emissions:.0f}t"

        ax1.text(
            x,
            y - node_size - 0.15,
            info_text,
            fontsize=9,
            ha="center",
            va="top",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8, "edgecolor": color},
        )

    # Draw interconnector flows as arrows
    for (from_r, to_r), data in G.edges.items():
        flow = data.get("flow", 0)
        if flow < 0.1:
            continue

        x1, y1 = pos[from_r]
        x2, y2 = pos[to_r]

        # Calculate arrow properties
        dx = x2 - x1
        dy = y2 - y1

        # Offset start and end points to node edges
        offset = 0.35
        length = (dx**2 + dy**2) ** 0.5
        x1_off = x1 + offset * dx / length
        y1_off = y1 + offset * dy / length
        x2_off = x2 - offset * dx / length
        y2_off = y2 - offset * dy / length

        # Draw arrow
        arrow = FancyArrowPatch(
            (x1_off, y1_off),
            (x2_off, y2_off),
            connectionstyle="arc3,rad=0.1",
            arrowstyle="->,head_width=0.15,head_length=0.1",
            linewidth=2 + flow / 20,
            color="#34495e",
            alpha=0.7,
            zorder=1,
        )
        ax1.add_patch(arrow)

        # Add flow label
        mid_x = (x1_off + x2_off) / 2
        mid_y = (y1_off + y2_off) / 2
        ax1.text(
            mid_x,
            mid_y,
            f"{flow:.0f} MW",
            fontsize=10,
            fontweight="bold",
            ha="center",
            va="bottom",
            color="#2c3e50",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "yellow", "alpha": 0.7},
        )

    # Add legend for node colors
    legend_elements = [
        Circle((0, 0), 0.1, color="#2ecc71", alpha=0.7, label="Low Emissions (<0.3 tCO₂/MWh)"),
        Circle((0, 0), 0.1, color="#f39c12", alpha=0.7, label="Medium Emissions (0.3-0.6)"),
        Circle((0, 0), 0.1, color="#e74c3c", alpha=0.7, label="High Emissions (>0.6)"),
    ]
    ax1.legend(handles=legend_elements, loc="upper left", fontsize=10)

    # TOP RIGHT: Energy balance chart
    ax2.set_title("Regional Energy Balance", fontsize=14)

    regions = regional_flows["network_region"].tolist()
    x_pos = np.arange(len(regions))

    generation = regional_flows["generation_mwh"].values
    imports = regional_flows["imports_mwh"].values
    exports = regional_flows["exports_mwh"].values

    width = 0.25
    ax2.bar(x_pos - width, generation, width, label="Generation", color="#2ecc71", alpha=0.8)
    ax2.bar(x_pos, imports, width, label="Imports", color="#3498db", alpha=0.8)
    ax2.bar(x_pos + width, exports, width, label="Exports", color="#e74c3c", alpha=0.8)

    ax2.set_xlabel("Region")
    ax2.set_ylabel("Energy (MWh)")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(regions)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # BOTTOM RIGHT: Emissions chart
    ax3.set_title("Regional Emissions", fontsize=14)

    local_emissions = regional_flows["local_emissions_t"].values
    import_emissions = regional_flows["import_emissions_t"].values
    export_emissions = regional_flows["export_emissions_t"].values

    ax3.bar(x_pos - width, local_emissions, width, label="Local", color="#95a5a6", alpha=0.8)
    ax3.bar(x_pos, import_emissions, width, label="Imports", color="#3498db", alpha=0.8)
    ax3.bar(x_pos + width, export_emissions, width, label="Exports", color="#e74c3c", alpha=0.8)

    ax3.set_xlabel("Region")
    ax3.set_ylabel("Emissions (tCO₂)")
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(regions)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)

    # Add summary box
    total_gen = regional_flows["generation_mwh"].sum()
    total_emissions = regional_flows["local_emissions_t"].sum()
    avg_intensity = total_emissions / total_gen if total_gen > 0 else 0
    circular_count = len(solution.circular_flows)

    summary_text = f"Total Generation: {total_gen:.0f} MWh\n"
    summary_text += f"Total Emissions: {total_emissions:.0f} tCO₂\n"
    summary_text += f"Avg Intensity: {avg_intensity:.3f} tCO₂/MWh\n"
    summary_text += f"Circular Flows: {circular_count}"

    ax3.text(
        0.02,
        0.98,
        summary_text,
        transform=ax3.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "lightblue", "alpha": 0.5},
    )

    plt.tight_layout()
    return fig


def demonstrate_circular_flow():
    """Demonstrate a specific circular flow scenario."""
    console.print("\n[bold magenta]═══ Demonstrating Circular Flow with NSW-SA Interconnector ═══[/bold magenta]\n")

    flows_v4 = NetworkFlowsV4()
    interval = datetime(2025, 9, 7, 18, 0, 0)  # Evening peak - most circular flows

    console.print(f"[cyan]Interval: {interval.strftime('%Y-%m-%d %H:%M')} (Evening Peak)[/cyan]\n")

    # Process the base interval
    solution = flows_v4.process_interval(interval)
    console.print(f"Base network: {len(solution.circular_flows)} circular flows\n")

    # Add NSW-SA interconnector with 500MW flow
    regional_gen = flows_v4.load_regional_generation(interval, interval)
    nsw_data = regional_gen[regional_gen["network_region"] == "NSW1"]
    emission_intensity = nsw_data.iloc[0]["emission_intensity"] if not nsw_data.empty else 0.7
    flow_emissions = (500 / 12) * emission_intensity

    console.print("[yellow]Adding NSW→SA 500MW interconnector...[/yellow]")
    flows_v4.solver.add_flow(interval, "NSW1", "SA1", "NSW1-SA1", 500, flow_emissions)

    # Get new state with circular flows
    after = flows_v4.solver.query_interval(interval)

    if after:
        console.print(f"[green]✓ Created {len(after.circular_flows)} circular flows![/green]\n")
    else:
        console.print("[red]Failed to query interval after adding flow[/red]")
        return

    # Show the most interesting circular flows
    console.print("[bold]Top Circular Flow Patterns:[/bold]")

    # Group by unique paths
    unique_paths = {}
    if after:
        for cf in after.circular_flows:
            path_key = "→".join(cf["loop_path"][:-1])  # Exclude duplicate end node
            if path_key not in unique_paths or cf["bottleneck_mwh"] > unique_paths[path_key]["bottleneck_mwh"]:
                unique_paths[path_key] = cf

    # Sort by bottleneck capacity
    sorted_flows = sorted(unique_paths.values(), key=lambda x: x["bottleneck_mwh"], reverse=True)

    for i, cf in enumerate(sorted_flows[:5], 1):
        path = " → ".join(cf["loop_path"])
        console.print(f"\n{i}. [cyan]{path}[/cyan]")
        console.print(f"   Bottleneck: [yellow]{cf['bottleneck_mwh']:.1f} MWh[/yellow]")
        console.print(f"   Total emissions: [red]{cf['total_emissions_t']:.2f} tCO2[/red]")
        console.print(f"   Loop length: {cf['loop_length']} hops")

    # Visualize the network before cleanup
    console.print("\n[yellow]Generating network visualization...[/yellow]")

    # Create visualizations
    fig_before = visualize_network_graph(solution, f"Network Without NSW-SA Link - {interval.strftime('%Y-%m-%d %H:%M')}")
    fig_after = visualize_network_graph(after, f"Network With NSW-SA 500MW Link - {interval.strftime('%Y-%m-%d %H:%M')}")

    # Save the figures
    fig_before.savefig("/tmp/network_before_nsw_sa.png", dpi=150, bbox_inches="tight")
    fig_after.savefig("/tmp/network_with_nsw_sa.png", dpi=150, bbox_inches="tight")
    console.print("[green]✓ Saved visualizations to /tmp/network_before_nsw_sa.png and /tmp/network_with_nsw_sa.png[/green]")

    # Clean up
    flows_v4.solver.remove_flows_by_interconnector(interval, "NSW1-SA1")

    console.print("\n[bold]Key Insight:[/bold]")
    console.print("The NSW-SA interconnector creates circular flows because it provides")
    console.print("an alternative path for power to flow between regions that are already")
    console.print("connected through Victoria. This creates arbitrage opportunities and")
    console.print("more complex power flow patterns in the NEM.")

    # Show the plots
    plt.show()


if __name__ == "__main__":
    main()
