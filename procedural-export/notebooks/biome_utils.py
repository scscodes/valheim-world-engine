"""
Biome Analysis Utilities
=========================

Shared utility functions for all biome analysis notebooks.

This module provides:
- Data loading and conversion
- Filter implementations (ported from renderer.js)
- Statistical analysis functions
- Visualization utilities
- Distance and coordinate calculations

Usage:
    from biome_utils import *
    df = load_samples('path/to/samples.json')
    df_filtered = apply_mistlands_recovery(df)
    plot_biome_distribution(df_filtered)
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional

# Import configuration
from config import *

# ============================================================================
# DATA LOADING AND CONVERSION
# ============================================================================

def load_samples(file_path: str) -> pd.DataFrame:
    """
    Load sample data from JSON file and convert to pandas DataFrame.

    Args:
        file_path: Path to samples JSON file (e.g., 'hkLycKKCMI-samples-1024.json')

    Returns:
        pandas DataFrame with columns: X, Z, Biome, Height, Distance

    Example:
        >>> df = load_samples('../output/samples/hkLycKKCMI-samples-1024.json')
        >>> print(df.head())
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Sample file not found: {file_path}")

    print(f"Loading samples from: {file_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Extract metadata
    world_name = data.get('WorldName', 'Unknown')
    resolution = data.get('Resolution', 0)
    sample_count = data.get('SampleCount', 0)

    # Convert samples to DataFrame
    samples = data['Samples']
    df = pd.DataFrame(samples)

    # Add computed distance from center
    df['Distance'] = np.sqrt(df['X']**2 + df['Z']**2)

    # Store metadata as DataFrame attributes
    df.attrs['world_name'] = world_name
    df.attrs['resolution'] = resolution
    df.attrs['sample_count'] = sample_count
    df.attrs['source_file'] = str(path)

    print(f"✓ Loaded {len(df):,} samples")
    print(f"✓ World: {world_name}")
    print(f"✓ Resolution: {resolution}×{resolution}")

    return df


def samples_to_grid(df: pd.DataFrame, resolution: int) -> np.ndarray:
    """
    Convert DataFrame to 2D grid for spatial operations.

    Args:
        df: Sample DataFrame
        resolution: Grid resolution (e.g., 512, 1024)

    Returns:
        3D numpy array of shape (resolution, resolution, 4)
        where [:, :, 0] = X, [:, :, 1] = Z, [:, :, 2] = Biome, [:, :, 3] = Height
    """
    grid = np.zeros((resolution, resolution, 4))

    # Samples should be in row-major order
    idx = 0
    for x in range(resolution):
        for z in range(resolution):
            if idx < len(df):
                sample = df.iloc[idx]
                grid[x, z, 0] = sample['X']
                grid[x, z, 1] = sample['Z']
                grid[x, z, 2] = sample['Biome']
                grid[x, z, 3] = sample['Height']
                idx += 1

    return grid


# ============================================================================
# FILTER IMPLEMENTATIONS (from renderer.js)
# ============================================================================

def apply_ocean_land_fix(df: pd.DataFrame, sea_level: float = SEA_LEVEL_METERS) -> pd.DataFrame:
    """
    Filter #1: Fix Ocean misclassification on above-water land.

    Problem: Distant lands (>7,900m) are classified as Ocean by API based on
    distance alone, even if terrain is above sea level.

    Solution: If biome==Ocean AND height >= sea_level, reclassify as Mistlands.

    Args:
        df: Input DataFrame
        sea_level: Height threshold for water (default: 30m)

    Returns:
        DataFrame with Ocean→Mistlands reclassification applied

    Reference: renderer.js lines 265-267
    """
    df = df.copy()

    mask = (df['Biome'] == 32) & (df['Height'] >= sea_level)
    count = mask.sum()

    if count > 0:
        df.loc[mask, 'Biome'] = 64  # Ocean → Mistlands

    df.attrs['ocean_land_fix_count'] = count

    return df


def apply_polar_water_fix(df: pd.DataFrame, sea_level: float = SEA_LEVEL_METERS) -> pd.DataFrame:
    """
    Filter #2: Distinguish deep water in polar biomes from polar land.

    Problem: DeepNorth/Ashlands can be underwater (true ocean) or above water (land).
    Deep water in these biomes should render as Ocean, not polar biome.

    Solution: If biome==DeepNorth/Ashlands AND height < (sea_level - 10), reclassify as Ocean.

    Args:
        df: Input DataFrame
        sea_level: Height threshold (default: 30m)

    Returns:
        DataFrame with polar→Ocean reclassification applied

    Reference: renderer.js lines 271-273
    """
    df = df.copy()

    deep_water_threshold = sea_level - 10
    mask = ((df['Biome'] == 256) | (df['Biome'] == 512)) & (df['Height'] < deep_water_threshold)
    count = mask.sum()

    if count > 0:
        df.loc[mask, 'Biome'] = 32  # Polar → Ocean

    df.attrs['polar_water_fix_count'] = count

    return df


def apply_mistlands_recovery(df: pd.DataFrame,
                             outer_ring_min: float = 6000,
                             outer_ring_max: float = 10000,
                             polar_threshold: float = 7000) -> pd.DataFrame:
    """
    Filter #3: Recover Mistlands from polar biomes in outer ring.

    Problem: Ashlands/DeepNorth are checked BEFORE Mistlands in GetBiome(),
    so they "steal" the outer ring (6-10km) where Mistlands should dominate.

    Solution: In outer ring, convert polar biomes → Mistlands, EXCEPT:
    - Keep Ashlands in far south (Z < -polar_threshold)
    - Keep DeepNorth in far north (Z > polar_threshold)

    This creates realistic polar crescents at poles while recovering Mistlands.

    Args:
        df: Input DataFrame
        outer_ring_min: Start of outer ring (default: 6000m)
        outer_ring_max: End of outer ring (default: 10000m)
        polar_threshold: Latitude cutoff for polar crescents (default: 7000m)

    Returns:
        DataFrame with Mistlands recovery applied

    Reference: renderer.js lines 280-313
    """
    df = df.copy()

    # Identify outer ring samples
    in_outer_ring = (df['Distance'] >= outer_ring_min) & (df['Distance'] <= outer_ring_max)

    # Ashlands: Keep only in far south (Z < -polar_threshold)
    ashlands_to_convert = in_outer_ring & (df['Biome'] == 512) & (df['Z'] >= -polar_threshold)

    # DeepNorth: Keep only in far north (Z > polar_threshold)
    deepnorth_to_convert = in_outer_ring & (df['Biome'] == 256) & (df['Z'] <= polar_threshold)

    # Apply conversions
    total_converted = ashlands_to_convert.sum() + deepnorth_to_convert.sum()

    if ashlands_to_convert.sum() > 0:
        df.loc[ashlands_to_convert, 'Biome'] = 64  # → Mistlands

    if deepnorth_to_convert.sum() > 0:
        df.loc[deepnorth_to_convert, 'Biome'] = 64  # → Mistlands

    df.attrs['mistlands_recovery_count'] = total_converted
    df.attrs['mistlands_recovery_params'] = {
        'outer_ring_min': outer_ring_min,
        'outer_ring_max': outer_ring_max,
        'polar_threshold': polar_threshold
    }

    return df


def apply_all_filters(df: pd.DataFrame,
                      sea_level: float = SEA_LEVEL_METERS,
                      polar_threshold: float = 7000) -> pd.DataFrame:
    """
    Apply all three filters in sequence.

    This is the full filter pipeline currently used in renderer.js.

    Args:
        df: Input DataFrame
        sea_level: Height threshold for water (default: 30m)
        polar_threshold: Latitude cutoff for polar crescents (default: 7000m)

    Returns:
        Fully filtered DataFrame
    """
    df = (df
          .pipe(apply_ocean_land_fix, sea_level=sea_level)
          .pipe(apply_polar_water_fix, sea_level=sea_level)
          .pipe(apply_mistlands_recovery, polar_threshold=polar_threshold)
         )

    return df


# ============================================================================
# STATISTICAL ANALYSIS
# ============================================================================

def calculate_biome_distribution(df: pd.DataFrame) -> Dict:
    """
    Calculate biome distribution statistics.

    Args:
        df: Sample DataFrame

    Returns:
        Dictionary with biome statistics:
        {
            'Meadows': {'count': 12345, 'percentage': 2.5, 'biome_id': 1},
            ...
        }
    """
    total = len(df)
    biome_counts = df['Biome'].value_counts()

    stats = {}
    for biome_id, count in biome_counts.items():
        name = get_biome_name(biome_id)
        percentage = (count / total) * 100
        stats[name] = {
            'count': count,
            'percentage': percentage,
            'biome_id': biome_id
        }

    return stats


def analyze_by_distance_ring(df: pd.DataFrame, rings: List[Tuple] = None) -> Dict:
    """
    Analyze biome distribution by distance rings.

    Args:
        df: Sample DataFrame
        rings: List of (min_dist, max_dist, label) tuples
               If None, uses ANALYSIS_RINGS from config

    Returns:
        Dictionary with ring statistics:
        {
            'Center (0-2km)': {
                'total': 12345,
                'biomes': {'Meadows': {'count': 5000, 'percentage': 40.5}, ...}
            },
            ...
        }
    """
    if rings is None:
        rings = ANALYSIS_RINGS

    stats = {}

    for min_dist, max_dist, label in rings:
        ring_samples = df[(df['Distance'] >= min_dist) & (df['Distance'] < max_dist)]
        total = len(ring_samples)

        if total == 0:
            continue

        biome_counts = ring_samples['Biome'].value_counts()

        ring_stats = {
            'total': total,
            'biomes': {}
        }

        for biome_id, count in biome_counts.items():
            name = get_biome_name(biome_id)
            percentage = (count / total) * 100
            ring_stats['biomes'][name] = {
                'count': count,
                'percentage': percentage
            }

        stats[label] = ring_stats

    return stats


def analyze_by_direction(df: pd.DataFrame) -> Dict:
    """
    Analyze biome distribution by compass direction.

    Args:
        df: Sample DataFrame

    Returns:
        Dictionary with directional statistics focusing on polar biomes
    """
    directions = {
        'North (Z > 0)': df['Z'] > 0,
        'South (Z < 0)': df['Z'] < 0,
        'East (X > 0)': df['X'] > 0,
        'West (X < 0)': df['X'] < 0
    }

    polar_biomes = [256, 512]  # DeepNorth, Ashlands

    stats = {}

    for direction, mask in directions.items():
        direction_samples = df[mask]
        total = len(direction_samples)

        dir_stats = {'total': total, 'biomes': {}}

        for biome_id in polar_biomes:
            biome_name = get_biome_name(biome_id)
            count = (direction_samples['Biome'] == biome_id).sum()
            total_biome = (df['Biome'] == biome_id).sum()

            pct_of_direction = (count / total) * 100 if total > 0 else 0
            pct_of_biome = (count / total_biome) * 100 if total_biome > 0 else 0

            dir_stats['biomes'][biome_name] = {
                'count': count,
                'pct_of_direction': pct_of_direction,
                'pct_of_biome': pct_of_biome
            }

        stats[direction] = dir_stats

    return stats


def count_biome(df: pd.DataFrame, biome_id: int) -> int:
    """
    Count samples of a specific biome.

    Args:
        df: Sample DataFrame
        biome_id: Biome ID to count

    Returns:
        Number of samples with this biome
    """
    return (df['Biome'] == biome_id).sum()


def compare_distributions(df1: pd.DataFrame, df2: pd.DataFrame,
                          label1: str = "Before", label2: str = "After") -> Tuple[Dict, Dict]:
    """
    Compare biome distributions between two DataFrames.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        label1: Label for first DataFrame
        label2: Label for second DataFrame

    Returns:
        Tuple of (stats1, stats2) dictionaries
    """
    stats1 = calculate_biome_distribution(df1)
    stats2 = calculate_biome_distribution(df2)

    print(f"\n{'Biome':<15} {label1:>10} {label2:>15} {'Change':>12}")
    print("-" * 60)

    all_biomes = set(list(stats1.keys()) + list(stats2.keys()))

    for biome in sorted(all_biomes):
        pct1 = stats1.get(biome, {}).get('percentage', 0)
        pct2 = stats2.get(biome, {}).get('percentage', 0)
        change = pct2 - pct1

        indicator = "↑" if change > 0 else "↓" if change < 0 else "="
        print(f"{biome:<15} {pct1:>9.2f}% {pct2:>14.2f}% {change:>11.2f}% {indicator}")

    return stats1, stats2


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_biome_distribution(df: pd.DataFrame, title: str = "Biome Distribution",
                            figsize: Tuple = (10, 8)) -> plt.Figure:
    """
    Plot biome distribution as pie chart.

    Args:
        df: Sample DataFrame
        title: Plot title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    stats = calculate_biome_distribution(df)

    # Sort by percentage descending
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['percentage'], reverse=True)

    labels = [name for name, _ in sorted_stats]
    sizes = [data['percentage'] for _, data in sorted_stats]
    colors = [get_biome_color(data['biome_id'], normalized=True) for _, data in sorted_stats]

    fig, ax = plt.subplots(figsize=figsize)

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                        autopct='%1.1f%%', startangle=90)

    # Make percentage text more readable
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    return fig


def plot_spatial_heatmap(df: pd.DataFrame, biome_id: Optional[int] = None,
                         title: Optional[str] = None, figsize: Tuple = (12, 12)) -> plt.Figure:
    """
    Plot spatial heatmap of biomes.

    Args:
        df: Sample DataFrame
        biome_id: If provided, show only this biome (others as gray)
        title: Plot title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    resolution = df.attrs.get('resolution', int(np.sqrt(len(df))))

    # Create color grid
    grid = np.zeros((resolution, resolution, 3))

    idx = 0
    for x in range(resolution):
        for z in range(resolution):
            if idx < len(df):
                sample = df.iloc[idx]
                sample_biome = sample['Biome']

                if biome_id is None:
                    # Show all biomes
                    color = get_biome_color(sample_biome, normalized=True)
                else:
                    # Show only target biome
                    if sample_biome == biome_id:
                        color = get_biome_color(biome_id, normalized=True)
                    else:
                        color = (0.8, 0.8, 0.8)  # Gray for others

                grid[x, z] = color
                idx += 1

    # Flip Y-axis so north is up
    grid = np.flip(grid, axis=1)

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(grid, origin='lower')
    ax.set_xlabel('X (West → East)', fontsize=12)
    ax.set_ylabel('Z (South → North)', fontsize=12)

    if title is None:
        if biome_id is not None:
            title = f"{get_biome_name(biome_id)} Distribution"
        else:
            title = "Biome Spatial Distribution"

    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    return fig


def plot_height_histogram(df: pd.DataFrame, bins: int = 100,
                          figsize: Tuple = (12, 6)) -> plt.Figure:
    """
    Plot height distribution histogram.

    Args:
        df: Sample DataFrame
        bins: Number of histogram bins
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(df['Height'], bins=bins, color=COLOR_SCHEME['primary'], alpha=0.7, edgecolor='black')

    # Add sea level line
    ax.axvline(SEA_LEVEL_METERS, color='red', linestyle='--', linewidth=2, label=f'Sea Level ({SEA_LEVEL_METERS}m)')

    ax.set_xlabel('Height (meters)', fontsize=12)
    ax.set_ylabel('Sample Count', fontsize=12)
    ax.set_title('Height Distribution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_distance_rings(df: pd.DataFrame, rings: List[Tuple] = None,
                        figsize: Tuple = (14, 8)) -> plt.Figure:
    """
    Plot biome distribution by distance rings.

    Args:
        df: Sample DataFrame
        rings: List of (min_dist, max_dist, label) tuples
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    if rings is None:
        rings = ANALYSIS_RINGS

    stats = analyze_by_distance_ring(df, rings)

    fig, axes = plt.subplots(2, 3, figsize=figsize)
    axes = axes.flatten()

    for idx, (label, ring_stats) in enumerate(stats.items()):
        if idx >= len(axes):
            break

        ax = axes[idx]

        biomes = ring_stats['biomes']
        sorted_biomes = sorted(biomes.items(), key=lambda x: x[1]['percentage'], reverse=True)

        labels = [name for name, _ in sorted_biomes]
        sizes = [data['percentage'] for _, data in sorted_biomes]
        colors = [get_biome_color(BIOME_NAME_TO_ID.get(name, 0), normalized=True)
                  for name, _ in sorted_biomes]

        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title(f"{label}\n({ring_stats['total']:,} samples)", fontsize=10, fontweight='bold')

    # Hide empty subplots
    for idx in range(len(stats), len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    return fig


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_world_bounds(df: pd.DataFrame) -> Dict:
    """
    Get world coordinate bounds.

    Args:
        df: Sample DataFrame

    Returns:
        Dictionary with min/max X, Z values
    """
    return {
        'x_min': df['X'].min(),
        'x_max': df['X'].max(),
        'z_min': df['Z'].min(),
        'z_max': df['Z'].max(),
        'height_min': df['Height'].min(),
        'height_max': df['Height'].max(),
        'distance_max': df['Distance'].max()
    }


def print_summary_stats(df: pd.DataFrame):
    """
    Print summary statistics for DataFrame.

    Args:
        df: Sample DataFrame
    """
    print("\n" + "="*60)
    print("SAMPLE DATA SUMMARY")
    print("="*60)

    print(f"\nWorld: {df.attrs.get('world_name', 'Unknown')}")
    print(f"Resolution: {df.attrs.get('resolution', 0)}×{df.attrs.get('resolution', 0)}")
    print(f"Total Samples: {len(df):,}")

    bounds = get_world_bounds(df)
    print(f"\nCoordinate Bounds:")
    print(f"  X: {bounds['x_min']:.1f} to {bounds['x_max']:.1f}")
    print(f"  Z: {bounds['z_min']:.1f} to {bounds['z_max']:.1f}")
    print(f"  Height: {bounds['height_min']:.1f} to {bounds['height_max']:.1f}")
    print(f"  Max Distance: {bounds['distance_max']:.1f}m")

    print(f"\nBiome Distribution:")
    stats = calculate_biome_distribution(df)
    for name, data in sorted(stats.items(), key=lambda x: x[1]['percentage'], reverse=True):
        print(f"  {name:<15} {data['count']:>8,} ({data['percentage']:>5.2f}%)")

    print("="*60 + "\n")


# ============================================================================
# EXPORT UTILITIES
# ============================================================================

def export_parameters_to_js(params: Dict, output_file: str = "optimized_params.js"):
    """
    Export optimized parameters as JavaScript code.

    Args:
        params: Dictionary of parameters to export
        output_file: Output file path
    """
    js_code = f"""// Optimized Biome Filter Parameters
// Generated from Jupyter notebook analysis

const FILTER_THRESHOLDS = {{
    // Sea level detection
    sea_level: {params.get('sea_level', SEA_LEVEL_METERS)},
    shoreline_depth: {params.get('shoreline_depth', -5.0)},

    // Mistlands recovery filter
    outer_ring_min: {params.get('outer_ring_min', 6000)},
    outer_ring_max: {params.get('outer_ring_max', 10000)},
    polar_threshold: {params.get('polar_threshold', 7000)},

    // Edge biome water distinction
    deep_water_threshold: {params.get('deep_water_threshold', 20)},
}};

// Copy these values to renderer.js lines 286-288, 305-307
"""

    with open(output_file, 'w') as f:
        f.write(js_code)

    print(f"✓ Exported parameters to {output_file}")
