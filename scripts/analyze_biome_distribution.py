#!/usr/bin/env python3
"""
Simple Biome Distribution Analysis
Analyzes JSON biome data and compares to expected distributions
"""

import json
import sys
from pathlib import Path
from collections import Counter

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

# Expected distributions for seed hkLycKKCMI (from reference)
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


def analyze_biome_json(json_path: Path):
    """Analyze biome distribution from JSON data"""
    print(f"\n{'='*80}")
    print(f"BIOME DISTRIBUTION ANALYSIS")
    print(f"{'='*80}\n")
    print(f"Data Source: {json_path}")
    print(f"Test Seed: hkLycKKCMI")
    print(f"Reference: docs/biomes_hnLycKKCMI.png (valheim-map.world)")

    with open(json_path, 'r') as f:
        data = json.load(f)

    biome_map = data.get('biome_map', [])
    resolution = data.get('resolution', 0)

    # Flatten the 2D array
    flat_biomes = [biome_id for row in biome_map for biome_id in row]

    # Count biomes
    biome_counts = Counter(flat_biomes)
    total_pixels = len(flat_biomes)

    # Detect invalid IDs
    invalid_ids = set(biome_counts.keys()) - VALID_BIOME_IDS

    print(f"\n{'Dataset Properties':<30}")
    print("-" * 50)
    print(f"{'Resolution:':<30} {resolution}x{resolution}")
    print(f"{'Total Pixels:':<30} {total_pixels:,}")
    print(f"{'Unique Biome IDs:':<30} {len(biome_counts)}")

    if invalid_ids:
        print(f"\n⚠️  INVALID BIOME IDs DETECTED: {sorted(invalid_ids)}")
        print(f"   JSON data contains non-bit-flag values!")
        return False
    else:
        print(f"{'Biome ID Validation:':<30} ✅ All valid")

    # Calculate distribution
    print(f"\n{'BIOME DISTRIBUTION'}")
    print("=" * 80)
    print(f"{'Biome':<15} {'Count':<12} {'Actual %':<12} {'Expected %':<12} {'Difference':<15}")
    print("-" * 80)

    has_large_deviation = False
    results = []

    for biome_id in sorted(VALID_BIOME_IDS):
        count = biome_counts.get(biome_id, 0)
        percentage = (count / total_pixels) * 100
        biome_name = BIOME_NAMES.get(biome_id, f"Unknown_{biome_id}")
        expected = EXPECTED_DISTRIBUTIONS.get(biome_name, 0.0)
        diff = percentage - expected

        results.append({
            'name': biome_name,
            'count': count,
            'percentage': percentage,
            'expected': expected,
            'diff': diff
        })

        # Flag significant deviations (>5%)
        if abs(diff) > 5.0:
            flag = "⚠️ "
            has_large_deviation = True
        else:
            flag = "✅ "

        print(f"{flag}{biome_name:<15} {count:<12,} {percentage:>6.2f}%      {expected:>6.1f}%      {diff:>+6.2f}%")

    # Analysis Summary
    print(f"\n{'ANALYSIS SUMMARY'}")
    print("=" * 80)

    if not invalid_ids:
        print("✅ No invalid biome IDs detected")
    else:
        print(f"❌ Invalid biome IDs: {sorted(invalid_ids)}")

    if has_large_deviation:
        print("⚠️  Large deviations (>5%) detected in biome distributions")
        print("\nBiomes with largest deviations:")
        top_deviations = sorted(results, key=lambda x: abs(x['diff']), reverse=True)[:3]
        for item in top_deviations:
            print(f"   - {item['name']}: {item['diff']:+.2f}% (expected {item['expected']:.1f}%, got {item['percentage']:.2f}%)")
    else:
        print("✅ All biome distributions within acceptable range")

    # Root cause note
    if has_large_deviation:
        print(f"\n{'POTENTIAL ROOT CAUSES'}")
        print("=" * 80)
        print("1. Sparse sampling density insufficient for accurate biome detection")
        print("   → DeepNorth and Ashlands over-represented suggests edge/boundary sampling bias")
        print("   → Ocean under-represented suggests large uniform areas being under-sampled")
        print("\n2. Adaptive sampling may be preferring high-variance areas")
        print("   → Biome boundaries get more samples than uniform regions")
        print("\n3. Interpolation or gap-filling logic")
        print("   → Check nearest-neighbor assignment for gaps between sparse samples")
        print("   → Verify no biome ID interpolation/blending occurs")

    print("\n" + "=" * 80)

    return not (invalid_ids or has_large_deviation)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_biome_distribution.py <biomes.json>")
        print("\nExample:")
        print("  python analyze_biome_distribution.py etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)

    success = analyze_biome_json(json_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
