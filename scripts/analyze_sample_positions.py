#!/usr/bin/env python3
"""
Analyze actual sample positions and biome distribution patterns
"""

import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np

BIOME_NAMES = {
    1: "Meadows",
    2: "Swamp",
    4: "Mountain",
    8: "BlackForest",
    16: "Plains",
    32: "Ocean",
    64: "Mistlands",
    256: "DeepNorth",
    512: "Ashlands"
}

def analyze_spatial_distribution(json_path: Path):
    """Analyze where biomes appear spatially"""

    with open(json_path, 'r') as f:
        data = json.load(f)

    biome_map = np.array(data['biome_map'])
    resolution = data['resolution']
    world_radius = data.get('world_radius', 10000)

    print(f"\n{'='*80}")
    print("SPATIAL DISTRIBUTION ANALYSIS")
    print(f"{'='*80}\n")

    # Analyze by radial zones (center, mid, edge)
    center_x, center_z = resolution // 2, resolution // 2

    # Calculate distance from center for each pixel
    distances = np.zeros_like(biome_map, dtype=float)
    for x in range(resolution):
        for z in range(resolution):
            dist = np.sqrt((x - center_x)**2 + (z - center_z)**2)
            distances[x, z] = dist

    max_dist = np.sqrt(2) * (resolution / 2)  # corner distance

    # Define zones
    zones = {
        'center': (0, max_dist * 0.33),
        'mid': (max_dist * 0.33, max_dist * 0.66),
        'edge': (max_dist * 0.66, max_dist)
    }

    print(f"Zone Definitions (in pixel units):")
    print(f"  Center: 0 to {zones['center'][1]:.1f} pixels from origin")
    print(f"  Mid:    {zones['mid'][0]:.1f} to {zones['mid'][1]:.1f} pixels")
    print(f"  Edge:   {zones['edge'][0]:.1f} to {max_dist:.1f} pixels")
    print()

    # Count biomes by zone
    zone_counts = {zone: Counter() for zone in zones.keys()}
    zone_totals = {zone: 0 for zone in zones.keys()}

    for x in range(resolution):
        for z in range(resolution):
            dist = distances[x, z]
            biome_id = biome_map[x, z]

            for zone_name, (min_dist, max_dist) in zones.items():
                if min_dist <= dist < max_dist:
                    zone_counts[zone_name][biome_id] += 1
                    zone_totals[zone_name] += 1
                    break

    # Print results
    print(f"{'BIOME DISTRIBUTION BY ZONE'}")
    print("=" * 100)
    print(f"{'Biome':<15} {'Center %':<12} {'Mid %':<12} {'Edge %':<12} {'Bias':<20}")
    print("-" * 100)

    biases = []
    for biome_id in sorted([1, 2, 4, 8, 16, 32, 64, 256, 512]):
        biome_name = BIOME_NAMES[biome_id]

        center_pct = (zone_counts['center'][biome_id] / zone_totals['center'] * 100) if zone_totals['center'] > 0 else 0
        mid_pct = (zone_counts['mid'][biome_id] / zone_totals['mid'] * 100) if zone_totals['mid'] > 0 else 0
        edge_pct = (zone_counts['edge'][biome_id] / zone_totals['edge'] * 100) if zone_totals['edge'] > 0 else 0

        # Calculate bias (edge vs center ratio)
        if center_pct > 0:
            bias = edge_pct / center_pct
            bias_str = f"{bias:.2f}x edge bias"
        else:
            bias = float('inf') if edge_pct > 0 else 0
            bias_str = "Edge-only" if edge_pct > 0 else "N/A"

        flag = "⚠️ " if bias > 2.0 and edge_pct > 5.0 else "  "

        print(f"{flag}{biome_name:<15} {center_pct:>6.2f}%      {mid_pct:>6.2f}%      {edge_pct:>6.2f}%      {bias_str:<20}")

        biases.append((biome_name, bias, edge_pct, center_pct))

    print()
    print(f"Zone sample counts:")
    print(f"  Center: {zone_totals['center']:,} pixels ({zone_totals['center']/sum(zone_totals.values())*100:.1f}%)")
    print(f"  Mid:    {zone_totals['mid']:,} pixels ({zone_totals['mid']/sum(zone_totals.values())*100:.1f}%)")
    print(f"  Edge:   {zone_totals['edge']:,} pixels ({zone_totals['edge']/sum(zone_totals.values())*100:.1f}%)")

    print(f"\n{'EDGE BIAS RANKING'}")
    print("=" * 80)
    biases_sorted = sorted([b for b in biases if b[1] != float('inf') and b[1] > 0], key=lambda x: x[1], reverse=True)
    for biome_name, bias, edge_pct, center_pct in biases_sorted[:5]:
        print(f"  {biome_name:<15} {bias:.2f}x (edge: {edge_pct:.2f}%, center: {center_pct:.2f}%)")

    print("\n" + "=" * 80)

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_sample_positions.py <biomes.json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)

    analyze_spatial_distribution(json_path)

if __name__ == '__main__':
    main()
