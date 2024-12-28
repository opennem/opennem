#!/usr/bin/env python
from pathlib import Path

import polars as pl


def detect_anomalies(
    df: pl.DataFrame,
    energy_window: int = 14,
    energy_threshold: float = 3.5,  # More conservative based on historical data
    facilities_window: int = 30,
    facilities_threshold: float = 3.0,  # More conservative
    min_std_threshold: float = 1e-6,  # Minimum standard deviation to consider
) -> pl.DataFrame:
    """
    Detect anomalies in energy and intervals data with different parameters for each metric

    Parameters:
    -----------
    df : pl.DataFrame
        DataFrame with columns: day, energy, intervals, facilities
    energy_window : int
        Size of rolling window for energy z-score calculation
    energy_threshold : float
        Number of standard deviations to consider energy anomalous
    facilities_window : int
        Size of rolling window for facilities z-score calculation
    facilities_threshold : float
        Number of standard deviations to consider facilities anomalous
    min_std_threshold : float
        Minimum standard deviation to consider for z-score calculation
    """
    # Filter for records before 2012 only
    df = df.filter(pl.col("day").str.contains("^[12]9[0-9][0-9]|^200[0-9]|^201[0-1]"))

    # For intervals, we know it should be 288 normally
    # Direct check for interval anomalies - only flag if significantly different (< 200)
    base = (
        df
        # Sort by date to ensure correct rolling calculations
        .sort("day")
        # Flag direct interval anomalies - more lenient with intervals
        .with_columns([(pl.col("intervals") < 200).alias("intervals_anomaly")])
    )

    # Calculate rolling stats with proper handling of edge cases
    with_stats = base.with_columns(
        [
            # Energy stats
            pl.col("energy").rolling_mean(energy_window, center=True).alias("energy_rolling_mean"),
            pl.col("energy")
            .rolling_std(energy_window, center=True)
            .map_elements(lambda x: max(x if x is not None else min_std_threshold, min_std_threshold), return_dtype=pl.Float64)
            .alias("energy_rolling_std"),
            # Facilities stats - using larger window and handling edge cases
            pl.col("facilities").rolling_mean(facilities_window, center=True).alias("facilities_rolling_mean"),
            pl.col("facilities")
            .rolling_std(facilities_window, center=True)
            .map_elements(lambda x: max(x if x is not None else min_std_threshold, min_std_threshold), return_dtype=pl.Float64)
            .alias("facilities_rolling_std"),
        ]
    )

    # Calculate z-scores and anomalies
    return (
        with_stats.with_columns(
            [
                # Energy z-score and anomaly
                ((pl.col("energy") - pl.col("energy_rolling_mean")) / pl.col("energy_rolling_std")).alias("energy_zscore"),
                # Facilities z-score
                ((pl.col("facilities") - pl.col("facilities_rolling_mean")) / pl.col("facilities_rolling_std")).alias(
                    "facilities_zscore"
                ),
            ]
        )
        .with_columns(
            [
                # Energy anomalies - using absolute z-score
                (pl.col("energy_zscore").abs() > energy_threshold).alias("energy_anomaly"),
                # Facilities anomalies - using absolute z-score
                (pl.col("facilities_zscore").abs() > facilities_threshold).alias("facilities_anomaly"),
            ]
        )
        # Add a combined anomaly flag - include all three types
        .with_columns(
            [(pl.col("energy_anomaly") | pl.col("intervals_anomaly") | pl.col("facilities_anomaly")).alias("is_anomaly")]
        )
    )


def analyze_energy_data(
    file_path: Path,
    energy_window: int = 14,
    energy_threshold: float = 3.5,  # More conservative
    facilities_window: int = 30,
    facilities_threshold: float = 3.0,  # More conservative
) -> pl.DataFrame:
    """
    Load data and perform anomaly detection with different parameters for each metric

    Parameters:
    -----------
    file_path : Path
        Path to CSV file with columns: day, energy, intervals, facilities
    energy_window : int
        Size of rolling window for energy z-score calculation
    energy_threshold : float
        Number of standard deviations to consider energy anomalous
    facilities_window : int
        Size of rolling window for facilities z-score calculation
    facilities_threshold : float
        Number of standard deviations to consider facilities anomalous
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read the CSV file
    df = pl.read_csv(file_path)

    # Detect anomalies
    results = detect_anomalies(
        df,
        energy_window=energy_window,
        energy_threshold=energy_threshold,
        facilities_window=facilities_window,
        facilities_threshold=facilities_threshold,
    )

    # Print summary of findings
    anomalies = results.filter(pl.col("is_anomaly"))
    print(f"\nFound {len(anomalies)} potential anomalies out of {len(results)} records")

    # Show anomalous records with details
    if len(anomalies) > 0:
        print("\nAnomalous records:")
        anomalies_df = anomalies.select(
            [
                "day",
                "energy",
                "intervals",
                "facilities",
                "energy_zscore",
                "facilities_zscore",
                "energy_anomaly",
                "intervals_anomaly",
                "facilities_anomaly",
            ]
        ).sort("day")

        print(anomalies_df)

        # Save anomalies to CSV
        output_path = file_path.parent / "energy_anomaly_output.csv"
        anomalies_df.write_csv(output_path)
        print(f"\nAnomalies saved to: {output_path}")

    return results


if __name__ == "__main__":
    # Using different parameters for each metric
    results = analyze_energy_data(
        Path(__file__).parent / "energy_data.csv",
        energy_window=14,
        energy_threshold=3.5,  # More conservative based on historical data
        facilities_window=30,
        facilities_threshold=3.0,  # Conservative for facility changes
    )
