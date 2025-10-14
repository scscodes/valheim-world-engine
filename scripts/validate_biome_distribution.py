#!/usr/bin/env python3
"""
Biome Distribution Validator
Analyzes biome maps for invalid IDs and distribution anomalies
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image

# Valid biome IDs (bit flags)
VALID_BIOME_IDS = {1, 2, 4, 8, 16, 32, 64, 256, 512}

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

# Expected distributions for seed hkLycKKCMI (reference values)
EXPECTED_DISTRIBUTIONS = {
    "Ocean": 30.0,
    "DeepNorth": 15.0,
    "Meadows": 12.0,
    "BlackForest": 10.0,
    "Plains": 10.0,
    "Mountain": 8.0,
    "Swamp": 7.0,
    "Mistlands": 5.0,
    "Ashlands": 3.0
}


def analyze_json_biome_data(json_path: Path) -> Dict:
    """Analyze biome distribution from JSON data"""
    print(f"\n{'='*80}")
    print(f"Analyzing JSON: {json_path}")
    print(f"{'='*80}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    biome_map = data.get('biome_map', [])
    if not biome_map:
        print("ERROR: No biome_map found in JSON")
        return {}

    # Flatten the 2D array
    flat_biomes = [biome_id for row in biome_map for biome_id in row]

    # Count biomes
    biome_counts = Counter(flat_biomes)
    total_pixels = len(flat_biomes)

    # Detect invalid IDs
    invalid_ids = set(biome_counts.keys()) - VALID_BIOME_IDS

    results = {
        'total_pixels': total_pixels,
        'unique_biome_ids': sorted(biome_counts.keys()),
        'invalid_ids': sorted(invalid_ids),
        'distribution': {},
        'has_errors': len(invalid_ids) > 0
    }

    print(f"\nTotal Pixels: {total_pixels:,}")
    print(f"Unique Biome IDs: {results['unique_biome_ids']}")

    if invalid_ids:
        print(f"\n⚠️  INVALID BIOME IDs DETECTED: {sorted(invalid_ids)}")
        print(f"   These IDs are not valid bit flags!")
        results['has_errors'] = True
    else:
        print("✅ All biome IDs are valid")

    # Calculate distribution
    print(f"\n{'Biome':<15} {'Count':<12} {'Percentage':<12} {'Expected':<12} {'Diff':<12}")
    print("-" * 80)

    for biome_id in sorted(VALID_BIOME_IDS):
        count = biome_counts.get(biome_id, 0)
        percentage = (count / total_pixels) * 100
        biome_name = BIOME_NAMES.get(biome_id, f"Unknown_{biome_id}")
        expected = EXPECTED_DISTRIBUTIONS.get(biome_name, 0.0)
        diff = percentage - expected

        results['distribution'][biome_name] = {
            'count': count,
            'percentage': percentage,
            'expected': expected,
            'diff': diff
        }

        # Flag significant deviations (>5%)
        flag = "⚠️ " if abs(diff) > 5.0 else "  "
        print(f"{flag}{biome_name:<15} {count:<12,} {percentage:>6.2f}%     {expected:>6.1f}%     {diff:>+6.2f}%")

    # List any invalid IDs with their counts
    if invalid_ids:
        print(f"\n{'Invalid ID':<15} {'Count':<12} {'Percentage':<12}")
        print("-" * 50)
        for invalid_id in sorted(invalid_ids):
            count = biome_counts[invalid_id]
            percentage = (count / total_pixels) * 100
            print(f"{invalid_id:<15} {count:<12,} {percentage:>6.2f}%")

    return results


def analyze_png_biome_data(png_path: Path) -> Dict:
    """Analyze biome distribution from PNG image"""
    print(f"\n{'='*80}")
    print(f"Analyzing PNG: {png_path}")
    print(f"{'='*80}")

    # Load PNG
    img = Image.open(png_path)
    img_array = np.array(img)

    print(f"Image Shape: {img_array.shape}")
    print(f"Image Mode: {img.mode}")

    # Reverse engineer biome IDs from colors
    # This is an approximation - PNG colors may not perfectly map back to IDs

    # Define color to biome mapping
    BIOME_COLORS = {
        1: (121, 176, 81),    # Meadows - green
        2: (119, 108, 92),    # Swamp - muddy brown
        4: (209, 228, 237),   # Mountain - light gray/white
        8: (88, 129, 59),     # BlackForest - dark green
        16: (229, 215, 150),  # Plains - tan/yellow
        32: (52, 97, 141),    # Ocean - blue
        64: (88, 90, 92),     # Mistlands - dark gray
        256: (255, 255, 255), # DeepNorth - white
        512: (139, 37, 28)    # Ashlands - dark red
    }

    # Create reverse mapping (color -> biome_id)
    color_to_biome = {}
    for biome_id, color in BIOME_COLORS.items():
        color_to_biome[color] = biome_id

    # Extract unique colors
    pixels = img_array.reshape(-1, 3)
    unique_colors = np.unique(pixels, axis=0)

    print(f"\nUnique Colors Found: {len(unique_colors)}")

    # Map colors to biome IDs
    biome_counts = Counter()
    unknown_colors = []

    for pixel in pixels:
        color_tuple = tuple(pixel)
        if color_tuple in color_to_biome:
            biome_counts[color_to_biome[color_tuple]] += 1
        else:
            # Unknown color - this indicates interpolation artifacts
            unknown_colors.append(color_tuple)

    total_pixels = len(pixels)
    unknown_count = len(unknown_colors)

    results = {
        'total_pixels': total_pixels,
        'unknown_color_pixels': unknown_count,
        'distribution': {},
        'has_errors': unknown_count > 0
    }

    if unknown_count > 0:
        # Count unique unknown colors
        unknown_counter = Counter(unknown_colors)
        print(f"\n⚠️  UNKNOWN COLORS DETECTED: {len(unknown_counter):,} unique colors")
        print(f"   Total pixels with unknown colors: {unknown_count:,} ({(unknown_count/total_pixels)*100:.2f}%)")
        print(f"   This indicates interpolation artifacts!")

        # Show top 10 unknown colors
        print(f"\n   Top 10 Unknown Colors:")
        for color, count in unknown_counter.most_common(10):
            print(f"   RGB{color}: {count:,} pixels ({(count/total_pixels)*100:.2f}%)")
    else:
        print("✅ All colors map to valid biomes")

    # Calculate distribution
    print(f"\n{'Biome':<15} {'Count':<12} {'Percentage':<12} {'Expected':<12} {'Diff':<12}")
    print("-" * 80)

    for biome_id in sorted(VALID_BIOME_IDS):
        count = biome_counts.get(biome_id, 0)
        percentage = (count / total_pixels) * 100
        biome_name = BIOME_NAMES.get(biome_id, f"Unknown_{biome_id}")
        expected = EXPECTED_DISTRIBUTIONS.get(biome_name, 0.0)
        diff = percentage - expected

        results['distribution'][biome_name] = {
            'count': count,
            'percentage': percentage,
            'expected': expected,
            'diff': diff
        }

        flag = "⚠️ " if abs(diff) > 5.0 else "  "
        print(f"{flag}{biome_name:<15} {count:<12,} {percentage:>6.2f}%     {expected:>6.1f}%     {diff:>+6.2f}%")

    return results


def compare_results(json_results: Dict, png_results: Dict):
    """Compare JSON vs PNG results"""
    print(f"\n{'='*80}")
    print("COMPARISON: JSON vs PNG")
    print(f"{'='*80}")

    print(f"\n{'Metric':<40} {'JSON':<20} {'PNG':<20}")
    print("-" * 80)
    print(f"{'Has Errors':<40} {str(json_results.get('has_errors', False)):<20} {str(png_results.get('has_errors', False)):<20}")
    print(f"{'Total Pixels':<40} {json_results.get('total_pixels', 0):<20,} {png_results.get('total_pixels', 0):<20,}")

    if json_results.get('invalid_ids'):
        print(f"{'Invalid Biome IDs':<40} {str(json_results['invalid_ids']):<20}")

    if png_results.get('unknown_color_pixels', 0) > 0:
        print(f"{'Unknown Color Pixels':<40} {'N/A':<20} {png_results['unknown_color_pixels']:<20,}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_biome_distribution.py <json_or_png_path> [additional_files...]")
        print("\nExample:")
        print("  python validate_biome_distribution.py data/seeds/hkLycKKCMI/processed/biomes.json")
        print("  python validate_biome_distribution.py data/seeds/hkLycKKCMI/renders/biomes_4096.png")
        print("  python validate_biome_distribution.py biomes.json biomes_4096.png")
        sys.exit(1)

    json_results = None
    png_results = None

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)

        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            continue

        if file_path.suffix == '.json':
            json_results = analyze_json_biome_data(file_path)
        elif file_path.suffix == '.png':
            png_results = analyze_png_biome_data(file_path)
        else:
            print(f"ERROR: Unsupported file type: {file_path.suffix}")

    # Compare if both provided
    if json_results and png_results:
        compare_results(json_results, png_results)

    # Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")

    has_any_errors = False

    if json_results:
        if json_results.get('has_errors'):
            print("❌ JSON contains invalid biome IDs")
            has_any_errors = True
        else:
            print("✅ JSON biome data is valid")

    if png_results:
        if png_results.get('has_errors'):
            print("❌ PNG contains interpolation artifacts (unknown colors)")
            has_any_errors = True
        else:
            print("✅ PNG biome data is valid")

    if has_any_errors:
        print("\n⚠️  VALIDATION FAILED: Errors detected")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED: No errors detected")
        sys.exit(0)


if __name__ == '__main__':
    main()
